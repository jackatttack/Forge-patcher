# -*- coding: utf-8 -*-
"""
guide_op.py
===========

Forge GUIDE op.

HELP answers: "What is this object?"
GUIDE answers: "How do we do this kind of work?"

Guides are small workflow recipes stored in forge/guides/*.txt.
They should grow from real successful sessions.
"""

import os
import re
import sys


SPEC = {
    'name': 'GUIDE',
    'target_kind': 'none',
    'body_mode': 'optional',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Show, search, add, or append workflow guides. Guides document repeatable Forge working patterns.',
    'subject': ['No subject. Use ARGS for commands.'],
    'common_failures': [
        'Unknown guide name — run GUIDE with ARGS: list.',
        'Missing BODY for add/append.',
        'Guide name contains unsafe characters.',
        'Brand-new GUIDE op may require REFRESH or one Pythonista restart before parser recognition.',
    ],
    'safe_usage': [
        'Use GUIDE when you know the goal but need the house workflow.',
        'Use HELP when you need reference for a specific op, file, or object.',
        'Keep guides short, practical, and action-shaped.',
        'When a workflow succeeds twice, consider adding or updating a guide.',
        'Do not turn one-off mistakes into permanent process unless they recur.',
    ],
    'minimal_example': [
        'GUIDE',
        'ARGS: list',
        '',
        'GUIDE',
        'ARGS: boot',
        '',
        'GUIDE',
        'ARGS: search branch',
    ],
    'related_ops': ['HELP', 'JOURNAL', 'FORGE_AUDIT', 'COMPAT_AUDIT', 'LIST_FILES'],
}

HINTS = {
    'guide': 'Run GUIDE with ARGS: list to see available guides.',
    'body': 'GUIDE add/append need body content.',
}

GUIDE_DIR = os.path.join('forge', 'guides')


def validate(parsed_op):
    raw = (parsed_op.directives.get('ARGS') or '').strip()
    body = parsed_op.body or ''

    parts = raw.split()
    cmd = parts[0].lower() if parts else 'boot'

    if cmd in ('add', 'append', 'replace') and not body.strip():
        return ['GUIDE %s requires BODY content.' % cmd]

    if cmd in ('add', 'append', 'replace', 'show') and len(parts) < 2:
        return ['GUIDE %s requires a guide name.' % cmd]

    if cmd not in ('boot', 'list', 'ls', 'show', 'search', 'add', 'append', 'replace'):
        if len(parts) == 1:
            return []
        return ['Unknown GUIDE command: %s. Use list, show, search, add, append, or replace.' % cmd]

    return []


def _root(ctx=None):
    if ctx is not None:
        return ctx.project_root
    try:
        from forge.config import DOCUMENTS_ROOT
        return DOCUMENTS_ROOT
    except Exception:
        return os.path.expanduser('~/Documents')


def _guide_dir(ctx=None):
    return os.path.join(_root(ctx), GUIDE_DIR)


def _slug(name):
    text = (name or '').strip().lower()
    text = text.replace('_', '-')
    text = re.sub(r'[^a-z0-9-]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    if not text:
        raise ValueError('Empty guide name.')
    return text


def _filename_for(name):
    return _slug(name).replace('-', '_') + '.txt'


def _path_for(ctx, name):
    return os.path.join(_guide_dir(ctx), _filename_for(name))


def _title_for_filename(filename):
    base = filename[:-4] if filename.endswith('.txt') else filename
    return base.replace('_', '-')


def _list_guides(ctx):
    """Return guide names in display order."""
    base = _guide_dir(ctx)
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        if name.endswith('.txt') and not name.startswith('.'):
            out.append(_title_for_filename(name))
    return out


def _summary_from_text(text):
    """Return a compact one-line summary from guide text."""
    lines = (text or '').splitlines()

    def clean(line):
        return ' '.join((line or '').strip().split())

    # Prefer explicit SUMMARY section.
    for i, line in enumerate(lines):
        if clean(line).upper() == '## SUMMARY':
            for sub in lines[i + 1:]:
                value = clean(sub)
                if value and not value.startswith('#'):
                    return value
                if value.startswith('## '):
                    break

    # Fallback to first useful line under WHEN TO USE.
    for i, line in enumerate(lines):
        if clean(line).upper() == '## WHEN TO USE':
            for sub in lines[i + 1:]:
                value = clean(sub)
                if value and not value.startswith('#'):
                    return value
                if value.startswith('## '):
                    break

    # Final fallback: first non-heading content line.
    for line in lines:
        value = clean(line)
        if value and not value.startswith('#'):
            return value

    return ''

def _read_guide(ctx, name):
    path = _path_for(ctx, name)
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().rstrip()


def _write_guide(ctx, name, body, mode='replace'):
    base = _guide_dir(ctx)
    os.makedirs(base, exist_ok=True)
    path = _path_for(ctx, name)
    text = (body or '').rstrip() + '\n'

    if mode == 'append' and os.path.exists(path):
        with open(path, 'a', encoding='utf-8') as f:
            if os.path.getsize(path) > 0:
                f.write('\n')
            f.write(text)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    return path


def _render_list(ctx):
    """Render available guides with one-line summaries."""
    guides = _list_guides(ctx)
    lines = ['=== GUIDES ===']
    if not guides:
        lines.append('- none')
    else:
        width = max([len(name) for name in guides] + [4])
        for name in guides:
            summary = _summary_from_text(_read_guide(ctx, name) or '')
            if summary:
                lines.append('- %-*s  %s' % (width, name, summary))
            else:
                lines.append('- ' + name)
    lines += [
        '',
        'USE:',
        'GUIDE',
        'ARGS: <name>',
        '',
        'GUIDE',
        'ARGS: search <term>',
    ]
    return '\n'.join(lines)


def _render_search(ctx, query):
    q = (query or '').strip().lower()
    lines = ['=== GUIDE SEARCH ===', 'query=%s' % (query or ''), '']

    if not q:
        lines.append('No query supplied.')
        return '\n'.join(lines)

    hits = []
    for name in _list_guides(ctx):
        text = _read_guide(ctx, name) or ''
        hay = (name + '\n' + text).lower()
        if q in hay:
            score = hay.count(q)
            snippet = ''
            for line in text.splitlines():
                if q in line.lower():
                    snippet = line.strip()
                    break
            hits.append((score, name, snippet))

    hits.sort(key=lambda x: (-x[0], x[1]))

    if not hits:
        lines.append('- no matches')
    else:
        for score, name, snippet in hits[:12]:
            lines.append('- %s  score=%s' % (name, score))
            if snippet:
                lines.append('  %s' % snippet[:140])

    return '\n'.join(lines)


def execute(ctx, parsed_op, result):
    raw = (parsed_op.directives.get('ARGS') or '').strip()
    body = parsed_op.body or ''

    parts = raw.split()
    if not parts:
        cmd = 'boot'
        rest = []
    else:
        cmd = parts[0].lower()
        rest = parts[1:]

    try:
        if cmd in ('list', 'ls'):
            result['status'] = 'APPLIED'
            result['message'] = 'listed guides'
            result['preview'] = _render_list(ctx)
            return

        if cmd == 'search':
            query = ' '.join(rest)
            result['status'] = 'APPLIED'
            result['message'] = 'searched guides'
            result['preview'] = _render_search(ctx, query)
            return

        if cmd in ('add', 'replace'):
            name = rest[0]
            path = _write_guide(ctx, name, body, mode='replace')
            result['status'] = 'APPLIED'
            result['message'] = 'saved guide: %s' % _slug(name)
            result['preview'] = 'Saved: %s' % os.path.relpath(path, ctx.project_root)
            return

        if cmd == 'append':
            name = rest[0]
            path = _write_guide(ctx, name, body, mode='append')
            result['status'] = 'APPLIED'
            result['message'] = 'appended guide: %s' % _slug(name)
            result['preview'] = 'Updated: %s' % os.path.relpath(path, ctx.project_root)
            return

        if cmd == 'show':
            name = rest[0]
        elif cmd == 'boot':
            name = 'boot'
        else:
            name = raw

        text = _read_guide(ctx, name)
        if text is None:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = 'Guide not found: %s. Run GUIDE with ARGS: list.' % name
            return

        result['status'] = 'APPLIED'
        result['message'] = 'Guide: %s' % _slug(name)
        result['preview'] = text

    except Exception as e:
        result['status'] = 'FAILED'
        result['message'] = '%s: %s' % (type(e).__name__, e)


def _cli_main(argv):
    class DummyCtx(object):
        project_root = _root(None)

    class DummyOp(object):
        def __init__(self, args, body=''):
            self.directives = {'ARGS': args}
            self.body = body

    args = ' '.join(argv[1:]) if len(argv) > 1 else 'list'
    result = {}
    execute(DummyCtx(), DummyOp(args), result)
    print(result.get('message', ''))
    preview = result.get('preview')
    if preview:
        print(preview)
    return 0 if result.get('status') == 'APPLIED' else 1


if __name__ == '__main__':
    _cli_main(sys.argv)
