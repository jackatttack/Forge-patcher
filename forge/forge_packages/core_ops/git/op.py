# -*- coding: utf-8 -*-
"""
GIT op.

GitHub repo helper for Forge.

Uses the GitHub API directly so it works from Pythonista without a local git
binary. The token is read from a local file and is never printed.
"""

import base64
import difflib
import hashlib
import json
import os
import shlex
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_OWNER = 'jackatttack'
DEFAULT_REPO = 'Forge-patcher'
DEFAULT_BRANCH = 'main'
DEFAULT_TOKEN_FILE = 'forge2/private/github_token.txt'
API_BASE = 'https://api.github.com'


SPEC = {
    'name': 'GIT',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set([
        'ARGS',
        'OWNER',
        'REPO',
        'BRANCH',
        'TOKEN_FILE',
        'TIMEOUT',
        'PATH',
        'LOCAL',
        'REMOTE',
        'MESSAGE',
        'CONFIRM',
        'DRY_RUN',
        'LIMIT',
    ]),
    'required_directives': set(),
}


HELP = {
    'summary': 'Inspect and update the configured GitHub repo through the GitHub API.',
    'minimal_example': [
        'GIT status',
        '',
        'GIT commits',
        'LIMIT: 5',
        '',
        'GIT files',
        'PATH: workspaces/forge_reboot',
        '',
        'GIT diff',
        'LOCAL: workspaces/forge_reboot/README.txt',
        'REMOTE: README.txt',
        '',
        'GIT upload',
        'LOCAL: workspaces/forge_reboot/README.txt',
        'REMOTE: README.txt',
        'MESSAGE: Update README',
        'DRY_RUN: yes',
        '',
        'GIT upload',
        'LOCAL: workspaces/forge_reboot/README.txt',
        'REMOTE: README.txt',
        'MESSAGE: Update README',
        'CONFIRM: yes',
    ],
    'common_failures': [
        'Token file missing.',
        'Token file contains placeholder text instead of a real token.',
        'GitHub token lacks repo contents access.',
        'Owner, repo, branch, or remote path is wrong.',
        'Network unavailable on device.',
        'Upload/delete attempted without DRY_RUN: yes or CONFIRM: yes.',
    ],
    'safe_usage': [
        'Never paste the token into chat.',
        'Use GIT status before write actions.',
        'Use GIT diff before single-file upload.',
        'Use DRY_RUN: yes before CONFIRM: yes.',
        'Upload supports files and folders.',
        'Delete supports files and folders.',
        'Folder upload skips generated artifacts, scratch, private paths, caches, and secret-looking names.',
    ],
}


HINTS = {
    '_max_hints': 1,
    'token': {
        'message': 'GIT needs a usable local GitHub token file.',
        'why': 'The GitHub API requires authentication for private repos and write actions.',
        'example': ['GIT status', 'TOKEN_FILE: forge2/private/github_token.txt'],
        'next': [
            'Check the token file exists.',
            'Keep the token local. Do not paste it into chat.',
        ],
    },
    'confirm': {
        'message': 'GIT write actions require DRY_RUN: yes or CONFIRM: yes.',
        'why': 'Upload and delete write to GitHub and should be deliberate.',
        'example': [
            'GIT upload',
            'LOCAL: README.txt',
            'REMOTE: README.txt',
            'MESSAGE: Update README',
            'DRY_RUN: yes',
        ],
        'next': ['Dry-run first, then repeat with CONFIRM: yes if correct.'],
    },
    '404': {
        'message': 'GitHub returned 404.',
        'why': 'The repo, branch, or remote path may be wrong, or the token may not have access.',
        'next': ['Run GIT status.', 'Check OWNER, REPO, BRANCH, and PATH/REMOTE.'],
    },
    '401': {
        'message': 'GitHub authentication failed.',
        'why': 'The token may be missing, expired, malformed, or lack permission.',
        'next': ['Check the token file locally.', 'Do not paste the token into chat.'],
    },
}


def _truthy(value):
    return str(value or '').strip().lower() in ('yes', 'true', '1', 'y', 'on')


def _split_words(text):
    text = str(text or '').strip()
    if not text:
        return []
    try:
        return shlex.split(text)
    except Exception:
        return text.split()


def _directives(parsed_op):
    return parsed_op.get('directives') or {}


def _target(parsed_op):
    return parsed_op.get('target') or ''


def _subcommand(parsed_op):
    directives = _directives(parsed_op)
    raw = (directives.get('ARGS') or _target(parsed_op) or '').strip()
    parts = _split_words(raw)
    if not parts:
        return 'status', []
    return parts[0].lower(), parts[1:]


def validate(parsed_op):
    errors = []
    directives = _directives(parsed_op)
    sub, args = _subcommand(parsed_op)

    allowed = ('status', 'repo', 'branch', 'branches', 'commits', 'files', 'file', 'diff', 'upload', 'delete')
    if sub not in allowed:
        errors.append('GIT subcommand must be one of: ' + ', '.join(allowed))

    if parsed_op.get('body'):
        errors.append('GIT does not accept body content')

    if sub == 'diff':
        local, remote = _local_remote_from_args(directives, args)
        if not local:
            errors.append('GIT diff requires LOCAL or PATH')
        if not remote:
            errors.append('GIT diff requires REMOTE')

    if sub == 'upload':
        dry_run = _truthy(directives.get('DRY_RUN'))
        confirm = _truthy(directives.get('CONFIRM'))
        local, remote = _local_remote_from_args(directives, args)
        message = str(directives.get('MESSAGE') or '').strip()

        if not local:
            errors.append('GIT upload requires LOCAL or PATH')
        if not remote:
            errors.append('GIT upload requires REMOTE')
        if not message:
            errors.append('GIT upload requires MESSAGE')
        if not dry_run and not confirm:
            errors.append('GIT upload requires CONFIRM: yes unless DRY_RUN: yes')

    if sub == 'delete':
        dry_run = _truthy(directives.get('DRY_RUN'))
        confirm = _truthy(directives.get('CONFIRM'))
        remote = str(directives.get('REMOTE') or '').strip()
        message = str(directives.get('MESSAGE') or '').strip()

        if args and not remote:
            remote = args[0]

        if not remote:
            errors.append('GIT delete requires REMOTE')
        if not message:
            errors.append('GIT delete requires MESSAGE')
        if not dry_run and not confirm:
            errors.append('GIT delete requires CONFIRM: yes unless DRY_RUN: yes')

    return errors


def _project_root(ctx):
    return os.path.abspath((ctx or {}).get('project_root') or os.getcwd())


def _rel_path(ctx, rel):
    rel = str(rel or '').strip()
    if os.path.isabs(rel):
        raise RuntimeError('Local paths must be relative to project root')
    root = _project_root(ctx)
    abs_path = os.path.abspath(os.path.join(root, rel))
    root_abs = os.path.abspath(root)
    if not (abs_path == root_abs or abs_path.startswith(root_abs + os.sep)):
        raise RuntimeError('Local path escapes project root: %s' % rel)
    return abs_path


def _read_token(ctx, token_file):
    path = _rel_path(ctx, token_file)
    if not os.path.isfile(path):
        raise RuntimeError('Token file not found: %s' % token_file)

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        token_text = f.read().strip()

    lines = []
    for line in token_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        lines.append(stripped)

    token = lines[0] if lines else ''
    bad = ('paste', 'token goes here', 'github_pat_xxx', '<token>', 'your token', 'replace me')
    if not token or any(x in token.lower() for x in bad):
        raise RuntimeError('Token file exists but does not contain a usable token')

    return token


def _quote_path(path):
    path = str(path or '').strip().strip('/')
    if not path:
        return ''
    return '/'.join(urllib.parse.quote(part) for part in path.split('/'))


def _repo_path(owner, repo):
    return '/repos/%s/%s' % (urllib.parse.quote(owner), urllib.parse.quote(repo))


def _short(text, limit=90):
    text = str(text or '').strip().replace('\n', ' ')
    if len(text) <= limit:
        return text
    return text[:max(0, limit - 1)] + '…'


def _api_json(path, token, timeout=20, method='GET', payload=None):
    url = API_BASE + path
    data = None
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Forge-GIT-Op',
        'Authorization': 'Bearer ' + token,
        'X-GitHub-Api-Version': '2022-11-28',
    }

    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            return resp.getcode(), json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {'message': raw[:300]}
        return e.code, body


def _contents_path(owner, repo, path, branch):
    path = _quote_path(path)
    base = _repo_path(owner, repo) + '/contents'
    if path:
        base += '/' + path
    return base + '?ref=' + urllib.parse.quote(branch)


def _decode_remote_file(owner, repo, branch, repo_path, token, timeout):
    if not repo_path:
        raise RuntimeError('Remote path required')

    code, data = _api_json(_contents_path(owner, repo, repo_path, branch), token, timeout=timeout)
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('GitHub file failed: HTTP %s %s' % (code, _short(msg)))

    if not isinstance(data, dict) or data.get('type') != 'file':
        raise RuntimeError('GitHub path is not a file: %s' % repo_path)

    raw_b64 = (data.get('content') or '').replace('\n', '')
    raw = base64.b64decode(raw_b64)
    return data, raw


def _sha256(raw):
    return hashlib.sha256(raw or b'').hexdigest()


def _text_or_none(raw):
    try:
        return raw.decode('utf-8')
    except Exception:
        return None


def _local_remote_from_args(directives, args):
    local = str(directives.get('LOCAL') or directives.get('PATH') or '').strip()
    remote = str(directives.get('REMOTE') or '').strip()

    if args and not local:
        local = args[0]
    if len(args) > 1 and not remote:
        remote = args[1]
    if local and not remote:
        remote = local

    return local, remote


def _render_kv(title, rows):
    out = [title, '=' * len(title), '']
    for key, value in rows:
        out.append('%s: %s' % (key, value))
    return out


def _repo_status(owner, repo, branch, token, timeout):
    code, repo_json = _api_json(_repo_path(owner, repo), token, timeout=timeout)
    if code != 200:
        msg = repo_json.get('message') if isinstance(repo_json, dict) else ''
        raise RuntimeError('GitHub repo check failed: HTTP %s %s' % (code, _short(msg)))

    code, branch_json = _api_json(_repo_path(owner, repo) + '/branches/' + urllib.parse.quote(branch), token, timeout=timeout)
    if code != 200:
        msg = branch_json.get('message') if isinstance(branch_json, dict) else ''
        raise RuntimeError('GitHub branch check failed: HTTP %s %s' % (code, _short(msg)))

    commit = branch_json.get('commit') or {}
    commit_sha = commit.get('sha') or ''
    commit_obj = commit.get('commit') or {}
    message = commit_obj.get('message') or ''
    author = commit_obj.get('author') or {}

    data = {
        'repo': '%s/%s' % (owner, repo),
        'owner': owner,
        'repo_name': repo,
        'branch': branch,
        'private': repo_json.get('private'),
        'visibility': repo_json.get('visibility', 'unknown'),
        'default_branch': repo_json.get('default_branch'),
        'html_url': repo_json.get('html_url', ''),
        'latest_sha': commit_sha,
        'latest_sha_short': commit_sha[:12] if commit_sha else '',
        'latest_author': author.get('name') or '',
        'latest_date': author.get('date') or '',
        'latest_message': message,
    }

    rows = _render_kv('GitHub repo status', [
        ('repo', data['repo']),
        ('branch', branch),
        ('private', data['private']),
        ('visibility', data['visibility']),
        ('default_branch', data['default_branch']),
        ('html_url', data['html_url']),
        ('latest_sha', data['latest_sha_short'] or '(missing)'),
        ('latest_author', data['latest_author'] or '(unknown)'),
        ('latest_date', data['latest_date'] or '(unknown)'),
        ('latest_message', _short(message, 180)),
        ('token', 'loaded from local file, not printed'),
    ])
    return '\n'.join(rows).rstrip() + '\n', data


def _branches(owner, repo, token, timeout):
    code, data = _api_json(_repo_path(owner, repo) + '/branches', token, timeout=timeout)
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('GitHub branches failed: HTTP %s %s' % (code, _short(msg)))

    branches = []
    rows = ['GitHub branches', '===============', '']
    for item in data:
        name = item.get('name') or ''
        sha = ((item.get('commit') or {}).get('sha') or '')
        protected = bool(item.get('protected'))
        branches.append({'name': name, 'sha': sha, 'sha_short': sha[:12], 'protected': protected})
        rows.append('- %s  %s  protected=%s' % (name, sha[:12], protected))

    return '\n'.join(rows).rstrip() + '\n', {'branches': branches}


def _commits(owner, repo, branch, limit, token, timeout):
    limit = max(1, min(int(limit), 30))
    q = '?sha=%s&per_page=%d' % (urllib.parse.quote(branch), limit)
    code, data = _api_json(_repo_path(owner, repo) + '/commits' + q, token, timeout=timeout)
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('GitHub commits failed: HTTP %s %s' % (code, _short(msg)))

    commits = []
    rows = ['GitHub commits', '==============', '']
    for item in data:
        sha = item.get('sha') or ''
        commit = item.get('commit') or {}
        msg = commit.get('message') or ''
        author = commit.get('author') or {}
        row = {
            'sha': sha,
            'sha_short': sha[:12],
            'message': msg,
            'message_short': _short(msg, 100),
            'author': author.get('name') or '',
            'date': author.get('date') or '',
            'url': item.get('html_url') or '',
        }
        commits.append(row)
        rows.append('- %s  %s  %s' % (row['sha_short'], row['date'], row['message_short']))

    return '\n'.join(rows).rstrip() + '\n', {'commits': commits, 'limit': limit}


def _files(owner, repo, branch, repo_path, token, timeout):
    code, data = _api_json(_contents_path(owner, repo, repo_path, branch), token, timeout=timeout)
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('GitHub files failed: HTTP %s %s' % (code, _short(msg)))

    rows = _render_kv('GitHub files', [
        ('repo', '%s/%s' % (owner, repo)),
        ('branch', branch),
        ('path', repo_path or '.'),
    ])
    rows.append('')

    items = []
    if isinstance(data, dict):
        item = {
            'type': data.get('type', 'file'),
            'size': data.get('size'),
            'path': data.get('path', repo_path),
            'sha': data.get('sha') or '',
        }
        items.append(item)
        rows.append('%s  %s  %s' % (item['type'], item['size'] or '', item['path']))
    else:
        dirs = []
        files = []
        for item in data:
            packed = {
                'type': item.get('type') or '',
                'size': item.get('size'),
                'path': item.get('path') or '',
                'sha': item.get('sha') or '',
            }
            if packed['type'] == 'dir':
                dirs.append(packed)
            else:
                files.append(packed)

        for item in dirs + files:
            items.append(item)
            glyph = 'dir ' if item['type'] == 'dir' else 'file'
            size = '' if item['size'] is None else str(item['size']) + ' B'
            rows.append('- %s  %-9s  %s' % (glyph, size, item['path']))

    return '\n'.join(rows).rstrip() + '\n', {'path': repo_path or '.', 'items': items}


def _file(owner, repo, branch, repo_path, token, timeout):
    data, raw = _decode_remote_file(owner, repo, branch, repo_path, token, timeout)

    text = raw.decode('utf-8', 'replace')
    limit = 7000
    clipped = text
    clipped_chars = 0
    if len(clipped) > limit:
        clipped_chars = len(clipped) - limit
        clipped = clipped[:limit].rstrip()

    rows = _render_kv('GitHub file', [
        ('path', data.get('path', repo_path)),
        ('sha', (data.get('sha') or '')[:12]),
        ('size', '%s B' % data.get('size', '')),
    ])
    rows.append('')
    rows.append(clipped)
    if clipped_chars:
        rows.append('')
        rows.append('... clipped %d chars ...' % clipped_chars)

    return '\n'.join(rows).rstrip() + '\n', {
        'path': data.get('path', repo_path),
        'sha': data.get('sha') or '',
        'sha_short': (data.get('sha') or '')[:12],
        'size': data.get('size'),
        'content_preview': clipped,
        'clipped_chars': clipped_chars,
    }


def _diff(ctx, owner, repo, branch, args, parsed_op, token, timeout):
    local, remote = _local_remote_from_args(_directives(parsed_op), args)
    local_abs = _rel_path(ctx, local)

    if not os.path.isfile(local_abs):
        raise RuntimeError('Local file not found: %s' % local)

    with open(local_abs, 'rb') as f:
        local_raw = f.read()

    remote_exists = True
    remote_meta = {}
    remote_raw = b''

    try:
        remote_meta, remote_raw = _decode_remote_file(owner, repo, branch, remote, token, timeout)
    except RuntimeError as e:
        msg = str(e)
        if 'HTTP 404' not in msg:
            raise
        remote_exists = False

    local_hash = _sha256(local_raw)
    remote_hash = _sha256(remote_raw) if remote_exists else ''
    same = remote_exists and local_hash == remote_hash

    rows = _render_kv('GitHub diff', [
        ('repo', '%s/%s' % (owner, repo)),
        ('branch', branch),
        ('local', local),
        ('remote', remote),
        ('remote_exists', remote_exists),
        ('local_size', '%d B' % len(local_raw)),
        ('remote_size', '%d B' % len(remote_raw) if remote_exists else '(missing)'),
        ('same', same),
        ('local_sha256', local_hash[:16]),
        ('remote_sha256', remote_hash[:16] if remote_hash else '(missing)'),
    ])
    rows.append('')

    data = {
        'local': local,
        'remote': remote,
        'remote_exists': remote_exists,
        'same': same,
        'local_size': len(local_raw),
        'remote_size': len(remote_raw) if remote_exists else None,
        'local_sha256': local_hash,
        'remote_sha256': remote_hash,
        'remote_sha': remote_meta.get('sha') or '',
        'diff_lines': [],
        'clipped_lines': 0,
    }

    if not remote_exists:
        rows.append('Remote file does not exist yet.')
        rows.append('Upload would create a new file at the remote path.')
        return '\n'.join(rows).rstrip() + '\n', data

    if same:
        rows.append('No content difference.')
        return '\n'.join(rows).rstrip() + '\n', data

    local_text = _text_or_none(local_raw)
    remote_text = _text_or_none(remote_raw)

    if local_text is None or remote_text is None:
        rows.append('Binary or non-UTF8 difference. Text diff not shown.')
        return '\n'.join(rows).rstrip() + '\n', data

    diff_lines = list(difflib.unified_diff(
        remote_text.splitlines(),
        local_text.splitlines(),
        fromfile='remote/' + remote,
        tofile='local/' + local,
        lineterm=''
    ))

    limit = 220
    clipped = 0
    if len(diff_lines) > limit:
        clipped = len(diff_lines) - limit
        diff_lines = diff_lines[:limit]

    data['diff_lines'] = diff_lines
    data['clipped_lines'] = clipped

    rows.append('Unified diff: remote -> local')
    rows.append('----------------------------')
    rows.extend(diff_lines)
    if clipped:
        rows.append('')
        rows.append('... clipped %d diff lines ...' % clipped)

    return '\n'.join(rows).rstrip() + '\n', data


def _remote_file_sha(owner, repo, branch, remote_path, token, timeout):
    code, data = _api_json(_contents_path(owner, repo, remote_path, branch), token, timeout=timeout)
    if code == 404:
        return None
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('Remote SHA lookup failed: HTTP %s %s' % (code, _short(msg)))
    if not isinstance(data, dict) or data.get('type') != 'file':
        raise RuntimeError('Remote path exists but is not a file: %s' % remote_path)
    return data.get('sha')


_SKIP_UPLOAD_DIRS = set([
    '.git',
    '.hg',
    '.svn',
    '.Trash',
    '__pycache__',
    '.pytest_cache',
    'artifacts',
    'scratch',
    'private',
    'site-packages',
    'site-packages-2',
])

_SECRET_NAME_BITS = (
    'secret',
    'token',
    'password',
    'credential',
    'apikey',
    'api_key',
    'private_key',
    'github_token',
    '.forge_secrets',
)


def _normalise_remote(path):
    path = str(path or '').strip().replace('\\', '/')
    path = path.strip('/')
    if path in ('', '.'):
        return ''
    parts = [p for p in path.split('/') if p and p != '.']
    return '/'.join(parts)


def _remote_join(base, rel):
    base = _normalise_remote(base)
    rel = _normalise_remote(rel)
    if base and rel:
        return base + '/' + rel
    return base or rel


def _is_secret_like(rel):
    s = str(rel or '').replace('\\', '/').lower()
    return any(bit in s for bit in _SECRET_NAME_BITS)


def _iter_upload_files(ctx, local, remote):
    local = str(local or '').strip()
    remote = _normalise_remote(remote)
    local_abs = _rel_path(ctx, local)

    files = []
    skipped = []

    if os.path.isfile(local_abs):
        if _is_secret_like(local):
            skipped.append({'rel': local, 'reason': 'secret-like path'})
        else:
            files.append({
                'local': local,
                'local_abs': local_abs,
                'remote': remote or os.path.basename(local),
                'size': os.path.getsize(local_abs),
            })
        return 'file', files, skipped

    if not os.path.isdir(local_abs):
        raise RuntimeError('Local path not found: %s' % local)

    for dirpath, dirnames, filenames in os.walk(local_abs):
        kept_dirs = []
        for dirname in sorted(dirnames):
            child_abs = os.path.join(dirpath, dirname)
            child_rel = os.path.relpath(child_abs, local_abs).replace(os.sep, '/')
            display_rel = os.path.join(local, child_rel).replace(os.sep, '/')
            if dirname in _SKIP_UPLOAD_DIRS:
                skipped.append({'rel': display_rel, 'reason': 'generated/private/cache directory'})
                continue
            if _is_secret_like(display_rel):
                skipped.append({'rel': display_rel, 'reason': 'secret-like directory'})
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            file_abs = os.path.join(dirpath, filename)
            child_rel = os.path.relpath(file_abs, local_abs).replace(os.sep, '/')
            display_rel = os.path.join(local, child_rel).replace(os.sep, '/')

            if _is_secret_like(display_rel):
                skipped.append({'rel': display_rel, 'reason': 'secret-like file'})
                continue

            files.append({
                'local': display_rel,
                'local_abs': file_abs,
                'remote': _remote_join(remote, child_rel),
                'size': os.path.getsize(file_abs),
            })

    return 'folder', files, skipped


def _put_remote_file(owner, repo, branch, remote, raw, message, token, timeout):
    sha = _remote_file_sha(owner, repo, branch, remote, token, timeout)
    payload = {
        'message': message,
        'content': base64.b64encode(raw).decode('ascii'),
        'branch': branch,
    }
    if sha:
        payload['sha'] = sha

    code, response = _api_json(
        _repo_path(owner, repo) + '/contents/' + _quote_path(remote),
        token,
        timeout=timeout,
        method='PUT',
        payload=payload,
    )

    if code not in (200, 201):
        msg = response.get('message') if isinstance(response, dict) else ''
        raise RuntimeError('GitHub upload failed for %s: HTTP %s %s' % (remote, code, _short(msg, 180)))

    commit = response.get('commit') or {}
    content = response.get('content') or {}
    return {
        'status_code': code,
        'content_sha': content.get('sha') or '',
        'commit_sha': commit.get('sha') or '',
        'commit_url': commit.get('html_url') or '',
    }


def _upload(ctx, owner, repo, branch, args, parsed_op, token, timeout):
    directives = _directives(parsed_op)
    local, remote = _local_remote_from_args(directives, args)
    message = str(directives.get('MESSAGE') or '').strip()
    dry_run = _truthy(directives.get('DRY_RUN'))

    kind, files, skipped = _iter_upload_files(ctx, local, remote)

    if not files:
        raise RuntimeError('GIT upload found no uploadable files under: %s' % local)

    total_size = sum(int(item.get('size') or 0) for item in files)

    rows = _render_kv('GitHub upload', [
        ('repo', '%s/%s' % (owner, repo)),
        ('branch', branch),
        ('local', local),
        ('remote', _normalise_remote(remote) or '.'),
        ('kind', kind),
        ('files', len(files)),
        ('skipped', len(skipped)),
        ('size', '%d B' % total_size),
        ('message', message),
    ])
    rows.append('')

    data = {
        'local': local,
        'remote': _normalise_remote(remote),
        'kind': kind,
        'message': message,
        'size': total_size,
        'files': [
            {'local': item['local'], 'remote': item['remote'], 'size': item['size']}
            for item in files
        ],
        'skipped': skipped,
        'dry_run': dry_run,
        'wrote': False,
        'written': [],
        'failed': [],
        'commit_sha': '',
        'commit_url': '',
    }

    rows.append('Files:')
    limit = 120
    for item in files[:limit]:
        rows.append('- %s -> %s (%d B)' % (item['local'], item['remote'] or '.', item['size']))
    if len(files) > limit:
        rows.append('... clipped %d file(s) ...' % (len(files) - limit))

    if skipped:
        rows.append('')
        rows.append('Skipped:')
        for item in skipped[:40]:
            rows.append('- %s [%s]' % (item.get('rel'), item.get('reason')))
        if len(skipped) > 40:
            rows.append('... clipped %d skipped path(s) ...' % (len(skipped) - 40))

    rows.append('')

    if dry_run:
        rows.append('DRY RUN ONLY — no GitHub write performed.')
        rows.append('Next: rerun with CONFIRM: yes to upload.')
        return '\n'.join(rows).rstrip() + '\n', data

    latest_commit = {}
    for item in files:
        with open(item['local_abs'], 'rb') as f:
            raw = f.read()
        try:
            info = _put_remote_file(owner, repo, branch, item['remote'], raw, message, token, timeout)
            written = {
                'local': item['local'],
                'remote': item['remote'],
                'size': item['size'],
                'status_code': info.get('status_code'),
                'content_sha': info.get('content_sha') or '',
                'commit_sha': info.get('commit_sha') or '',
                'commit_url': info.get('commit_url') or '',
            }
            data['written'].append(written)
            latest_commit = info
        except Exception as e:
            failed = {'local': item['local'], 'remote': item['remote'], 'error': str(e)}
            data['failed'].append(failed)
            raise

    data['wrote'] = True
    data['commit_sha'] = latest_commit.get('commit_sha') or ''
    data['commit_url'] = latest_commit.get('commit_url') or ''

    rows.append('uploaded: yes')
    rows.append('written: %d' % len(data['written']))
    rows.append('failed: %d' % len(data['failed']))
    rows.append('latest_commit_sha: %s' % data['commit_sha'][:12])
    rows.append('latest_commit_url: %s' % data['commit_url'])

    return '\n'.join(rows).rstrip() + '\n', data


def _remote_entries_recursive(owner, repo, branch, remote, token, timeout):
    remote = _normalise_remote(remote)
    code, data = _api_json(_contents_path(owner, repo, remote, branch), token, timeout=timeout)

    if code == 404:
        raise RuntimeError('Remote path not found: %s' % (remote or '.'))
    if code != 200:
        msg = data.get('message') if isinstance(data, dict) else ''
        raise RuntimeError('GitHub remote listing failed: HTTP %s %s' % (code, _short(msg, 180)))

    if isinstance(data, dict):
        if data.get('type') != 'file':
            raise RuntimeError('Remote path is not a file or directory: %s' % (remote or '.'))
        return [{
            'path': data.get('path') or remote,
            'sha': data.get('sha') or '',
            'size': data.get('size'),
            'type': 'file',
        }], 'file'

    files = []
    for item in data:
        item_type = item.get('type') or ''
        item_path = item.get('path') or ''
        if item_type == 'file':
            files.append({
                'path': item_path,
                'sha': item.get('sha') or '',
                'size': item.get('size'),
                'type': 'file',
            })
        elif item_type == 'dir':
            child_files, _kind = _remote_entries_recursive(owner, repo, branch, item_path, token, timeout)
            files.extend(child_files)

    files.sort(key=lambda x: x.get('path') or '')
    return files, 'folder'


def _delete_remote_file(owner, repo, branch, remote, sha, message, token, timeout):
    payload = {'message': message, 'sha': sha, 'branch': branch}

    code, response = _api_json(
        _repo_path(owner, repo) + '/contents/' + _quote_path(remote),
        token,
        timeout=timeout,
        method='DELETE',
        payload=payload,
    )

    if code != 200:
        msg = response.get('message') if isinstance(response, dict) else ''
        raise RuntimeError('GitHub delete failed for %s: HTTP %s %s' % (remote, code, _short(msg, 180)))

    commit = response.get('commit') or {}
    return {
        'status_code': code,
        'commit_sha': commit.get('sha') or '',
        'commit_url': commit.get('html_url') or '',
    }


def _delete(ctx, owner, repo, branch, args, parsed_op, token, timeout):
    directives = _directives(parsed_op)
    remote = str(directives.get('REMOTE') or '').strip()
    message = str(directives.get('MESSAGE') or '').strip()
    dry_run = _truthy(directives.get('DRY_RUN'))

    if args and not remote:
        remote = args[0]

    remote = _normalise_remote(remote)
    files, kind = _remote_entries_recursive(owner, repo, branch, remote, token, timeout)

    rows = _render_kv('GitHub delete', [
        ('repo', '%s/%s' % (owner, repo)),
        ('branch', branch),
        ('remote', remote or '.'),
        ('kind', kind),
        ('files', len(files)),
        ('message', message),
    ])
    rows.append('')

    data = {
        'remote': remote,
        'kind': kind,
        'message': message,
        'files': files,
        'dry_run': dry_run,
        'wrote': False,
        'deleted': [],
        'failed': [],
        'commit_sha': '',
        'commit_url': '',
    }

    if not files:
        raise RuntimeError('Cannot delete: no remote files found under %s' % (remote or '.'))

    rows.append('Files:')
    limit = 120
    for item in files[:limit]:
        rows.append('- %s  %s B  %s' % (item.get('sha', '')[:12], item.get('size'), item.get('path')))
    if len(files) > limit:
        rows.append('... clipped %d file(s) ...' % (len(files) - limit))
    rows.append('')

    if dry_run:
        rows.append('DRY RUN ONLY — no GitHub delete performed.')
        rows.append('Next: rerun with CONFIRM: yes to delete.')
        return '\n'.join(rows).rstrip() + '\n', data

    latest_commit = {}
    for item in files:
        try:
            info = _delete_remote_file(
                owner,
                repo,
                branch,
                item.get('path') or '',
                item.get('sha') or '',
                message,
                token,
                timeout,
            )
            deleted = {
                'path': item.get('path') or '',
                'sha': item.get('sha') or '',
                'status_code': info.get('status_code'),
                'commit_sha': info.get('commit_sha') or '',
                'commit_url': info.get('commit_url') or '',
            }
            data['deleted'].append(deleted)
            latest_commit = info
        except Exception as e:
            failed = {'path': item.get('path') or '', 'error': str(e)}
            data['failed'].append(failed)
            raise

    data['wrote'] = True
    data['commit_sha'] = latest_commit.get('commit_sha') or ''
    data['commit_url'] = latest_commit.get('commit_url') or ''

    rows.append('deleted: yes')
    rows.append('deleted_files: %d' % len(data['deleted']))
    rows.append('failed: %d' % len(data['failed']))
    rows.append('latest_commit_sha: %s' % data['commit_sha'][:12])
    rows.append('latest_commit_url: %s' % data['commit_url'])

    return '\n'.join(rows).rstrip() + '\n', data


def _settings(parsed_op):
    directives = _directives(parsed_op)
    owner = str(directives.get('OWNER') or DEFAULT_OWNER).strip()
    repo = str(directives.get('REPO') or DEFAULT_REPO).strip()
    branch = str(directives.get('BRANCH') or DEFAULT_BRANCH).strip()
    token_file = str(directives.get('TOKEN_FILE') or DEFAULT_TOKEN_FILE).strip()

    try:
        timeout = int(str(directives.get('TIMEOUT') or '20').strip())
    except Exception:
        timeout = 20

    return owner, repo, branch, token_file, timeout


def execute(ctx, parsed_op, result):
    sub, args = _subcommand(parsed_op)
    owner, repo, branch, token_file, timeout = _settings(parsed_op)

    base_data = {
        'subcommand': sub,
        'args': args,
        'owner': owner,
        'repo': repo,
        'repo_full': '%s/%s' % (owner, repo),
        'branch': branch,
        'token_file': token_file,
        'token_loaded': False,
        'timeout': timeout,
    }

    try:
        token = _read_token(ctx, token_file)
        base_data['token_loaded'] = True

        if sub in ('status', 'repo', 'branch'):
            preview, extra = _repo_status(owner, repo, branch, token, timeout)
            message = 'GitHub status checked: %s/%s@%s' % (owner, repo, branch)

        elif sub == 'branches':
            preview, extra = _branches(owner, repo, token, timeout)
            message = 'GitHub branches listed: %s/%s' % (owner, repo)

        elif sub == 'commits':
            limit = _directives(parsed_op).get('LIMIT') or '10'
            preview, extra = _commits(owner, repo, branch, int(limit), token, timeout)
            message = 'GitHub commits listed: %s/%s@%s' % (owner, repo, branch)

        elif sub == 'files':
            repo_path = str(_directives(parsed_op).get('PATH') or '').strip()
            if args and not repo_path:
                repo_path = args[0]
            preview, extra = _files(owner, repo, branch, repo_path, token, timeout)
            message = 'GitHub files listed: %s/%s:%s' % (owner, repo, repo_path or '.')

        elif sub == 'file':
            repo_path = str(_directives(parsed_op).get('PATH') or '').strip()
            if args and not repo_path:
                repo_path = args[0]
            preview, extra = _file(owner, repo, branch, repo_path, token, timeout)
            message = 'GitHub file read: %s/%s:%s' % (owner, repo, repo_path)

        elif sub == 'diff':
            preview, extra = _diff(ctx, owner, repo, branch, args, parsed_op, token, timeout)
            message = 'GitHub diff checked: %s/%s@%s' % (owner, repo, branch)

        elif sub == 'upload':
            preview, extra = _upload(ctx, owner, repo, branch, args, parsed_op, token, timeout)
            if extra.get('wrote'):
                message = 'GitHub upload applied: %s/%s@%s' % (owner, repo, branch)
            else:
                message = 'GitHub upload dry-run: %s/%s@%s' % (owner, repo, branch)

        elif sub == 'delete':
            preview, extra = _delete(ctx, owner, repo, branch, args, parsed_op, token, timeout)
            if extra.get('wrote'):
                message = 'GitHub delete applied: %s/%s@%s' % (owner, repo, branch)
            else:
                message = 'GitHub delete dry-run: %s/%s@%s' % (owner, repo, branch)

        else:
            raise RuntimeError('Unsupported GIT subcommand: %s' % sub)

    except Exception as e:
        result['status'] = 'FAILED_RUNTIME'
        result['message'] = 'GIT failed: %s' % e
        result['preview'] = 'GIT %s\nfailed: %s' % (sub, e)
        base_data['error'] = str(e)
        result['data'] = base_data
        return

    data = dict(base_data)
    data.update(extra or {})

    result['status'] = 'APPLIED'
    result['message'] = message
    result['preview'] = preview
    result['data'] = data