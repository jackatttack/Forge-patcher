# -*- coding: utf-8 -*-
"""
PACK op.

Pack selected files into a portable self-installing Python script.

This is a reboot package port of the mature Forge2 PACK idea, adapted so
artifacts live inside the current Forge workspace:

    forge/artifacts/packed/
"""

import base64
import os


SPEC = {
    'name': 'PACK',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': set(['EXCLUDE', 'EXT', 'DRY_RUN', 'MODE', 'CONFIRM']),
    'required_directives': set(),
}


HELP = {
    'summary': 'Pack selected files into a portable self-installing Python script.',
    'minimal_example': [
        'PACK forge_public_check',
        'DRY_RUN: yes',
        'EXCLUDE: artifacts/, scratch/, private/, token, secret',
        'BEGIN_BODY',
        'forge/README.txt',
        'forge/forge_core/',
        'END_BODY',
        '',
        'PACK forge_public_folder',
        'MODE: folder',
        'EXCLUDE: artifacts/, scratch/, private/, token, secret',
        'BEGIN_BODY',
        'forge/README.txt',
        'forge/forge_core/',
        'END_BODY',
    ],
    'common_failures': [
        'Target name missing.',
        'No body paths supplied.',
        'Include path not found.',
        'Secret-looking files included by accident.',
        'Unsupported MODE.',
    ],
    'safe_usage': [
        'Use DRY_RUN: yes first.',
        'Use EXCLUDE for artifacts, scratch files, private files, tokens, caches, and device-local data.',
        'Use MODE: folder for large packs.',
        'Generated installers default to the current working directory, not the source device path.',
    ],
}


HINTS = {
    '_max_hints': 1,
    'body': {
        'message': 'PACK needs body paths.',
        'why': 'PACK must know which files or directories to include.',
        'example': [
            'PACK my_export',
            'DRY_RUN: yes',
            'BEGIN_BODY',
            'forge/README.txt',
            'END_BODY',
        ],
        'next': [
            'Add BEGIN_BODY / END_BODY with one include path per line.',
            'Run DRY_RUN: yes before writing a pack.',
        ],
    },
    'target': {
        'message': 'PACK needs an output name.',
        'why': 'The name becomes the generated installer or folder name.',
        'example': [
            'PACK forge_public',
            'DRY_RUN: yes',
            'BEGIN_BODY',
            'forge/README.txt',
            'END_BODY',
        ],
        'next': ['Put the pack name directly after PACK.'],
    },
    'mode': {
        'message': 'PACK MODE must be script or folder.',
        'why': 'Script mode writes one installer; folder mode writes a tiny launcher plus large payload.',
        'example': ['MODE: folder'],
        'next': ['Use MODE: script or MODE: folder.'],
    },
}


def validate(parsed_op):
    errors = []
    target = (parsed_op.get('target') or '').strip()

    if not target:
        errors.append('PACK requires a target name')

    if not (parsed_op.get('body') or '').strip():
        errors.append('PACK requires body content — list paths to include')

    mode = str((parsed_op.get('directives') or {}).get('MODE') or 'script').strip().lower()
    if mode in ('', 'default'):
        mode = 'script'
    if mode not in ('script', 'folder'):
        errors.append('PACK MODE must be script or folder')

    return errors


def _project_root(ctx):
    return os.path.abspath(ctx.get('project_root') or os.getcwd())


def _directives(parsed_op):
    return parsed_op.get('directives') or {}


def _truthy(value):
    return str(value or '').strip().lower() in ('1', 'yes', 'y', 'true', 'on')


def _safe_name(name):
    name = str(name or '').strip()
    if name.endswith('.py'):
        name = name[:-3]
    name = name.strip().strip('/').strip('\\')
    clean = ''.join(ch if ch.isalnum() or ch in ('_', '-', '.') else '_' for ch in name)
    return clean.strip('._') or 'pack'


def _parse_excludes(parsed_op):
    raw = _directives(parsed_op).get('EXCLUDE') or ''
    return [item.strip() for item in str(raw).split(',') if item.strip()]


def _parse_ext(parsed_op):
    raw = str(_directives(parsed_op).get('EXT') or '*').strip()
    if raw == '*':
        return None
    out = []
    for item in raw.split(','):
        item = item.strip().lstrip('.')
        if item:
            out.append(item.lower())
    return out


def _in_root(root, path):
    root_real = os.path.realpath(os.path.abspath(root))
    path_real = os.path.realpath(os.path.abspath(path))
    return path_real == root_real or path_real.startswith(root_real + os.sep)


def _should_exclude(rel, excludes):
    rel = str(rel or '').replace('\\', '/')
    rel_l = rel.lower()

    for ex in excludes:
        ex = str(ex or '').strip().replace('\\', '/')
        if not ex:
            continue
        ex_l = ex.lower()
        if rel_l == ex_l:
            return True
        if rel_l.startswith(ex_l.rstrip('/') + '/'):
            return True
        if ex_l in rel_l:
            return True

    if rel_l.endswith('.bak'):
        return True

    return False


def _is_secret_like(rel):
    s = str(rel or '').lower()
    risky = [
        'api_key',
        'apikey',
        'secret',
        'token',
        'password',
        'credential',
        'credentials',
        'private_key',
        'github_token',
        '.forge_secrets',
        '/private/',
        'private/',
    ]
    return any(item in s for item in risky)


def _collect_files(root, include_paths, excludes, exts):
    collected = []
    missing = []

    for raw in include_paths:
        rel_in = str(raw or '').strip()
        if not rel_in:
            continue

        if os.path.isabs(rel_in):
            missing.append((rel_in, 'absolute paths are not allowed'))
            continue

        abs_path = os.path.abspath(os.path.join(root, rel_in))
        if not _in_root(root, abs_path):
            missing.append((rel_in, 'escapes project root'))
            continue

        if os.path.isdir(abs_path):
            for dirpath, dirnames, filenames in os.walk(abs_path):
                dirnames[:] = sorted(
                    d for d in dirnames
                    if not d.startswith('.') and d != '__pycache__'
                )
                for fn in sorted(filenames):
                    if fn.startswith('.'):
                        continue
                    if exts is not None:
                        ext = fn.rsplit('.', 1)[-1].lower() if '.' in fn else ''
                        if ext not in exts:
                            continue
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, root).replace('\\', '/')
                    if not _should_exclude(rel, excludes):
                        collected.append(rel)
            continue

        if os.path.isfile(abs_path):
            rel = os.path.relpath(abs_path, root).replace('\\', '/')
            if not _should_exclude(rel, excludes):
                collected.append(rel)
            continue

        missing.append((rel_in, 'not found'))

    out = []
    seen = set()
    for rel in collected:
        if rel not in seen:
            seen.add(rel)
            out.append(rel)

    return out, missing


def _format_bytes(n):
    try:
        n = int(n or 0)
    except Exception:
        n = 0

    units = ['B', 'KB', 'MB', 'GB']
    value = float(n)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == 'B':
                return '%d B' % int(value)
            return '%.2f %s' % (value, unit)
        value /= 1024.0


def _forge_home(root):
    try:
        from forge_core.run_storage import forge_home
        return forge_home(root)
    except Exception:
        return os.path.abspath(root)


def _rel_from_root(root, abs_path):
    try:
        return os.path.relpath(abs_path, root).replace('\\', '/')
    except Exception:
        return abs_path.replace('\\', '/')


def _packed_root(root):
    return os.path.join(_forge_home(root), 'artifacts', 'packed')


def _packed_rel(root, *parts):
    return _rel_from_root(root, os.path.join(_packed_root(root), *parts))


def _build_installer(files_dict, out_name, files_meta):
    entries = []
    for rel, content in sorted(files_dict.items()):
        data = base64.b64encode((content or '').encode('utf-8')).decode('ascii')
        entries.append('    %r: %r,' % (rel, data))

    meta_entries = []
    for item in sorted(files_meta or [], key=lambda x: x.get('rel') or ''):
        meta_entries.append('    %r: %r,' % (item.get('rel'), int(item.get('bytes') or 0)))

    payload = '\n'.join(entries)
    meta_payload = '\n'.join(meta_entries)

    template = '''# -*- coding: utf-8 -*-
"""
@@OUT_NAME@@.py
===============

Self-installing Python pack generated by Forge PACK.

Usage:
  python @@OUT_NAME@@.py --help
  python @@OUT_NAME@@.py --list
  python @@OUT_NAME@@.py --dry-run
  python @@OUT_NAME@@.py --dry-run-here
  python @@OUT_NAME@@.py --dry-run-root PATH
  python @@OUT_NAME@@.py --install
  python @@OUT_NAME@@.py --install-here
  python @@OUT_NAME@@.py --install-root PATH

Running with no arguments installs to the current working directory.
"""

import base64
import os
import sys

PACK_NAME = @@PACK_NAME@@

FILES_B64 = {
@@PAYLOAD@@
}

FILE_SIZES = {
@@META_PAYLOAD@@
}


def _decode(text):
    return base64.b64decode(text.encode('ascii')).decode('utf-8')


def _format_bytes(n):
    try:
        n = int(n or 0)
    except Exception:
        n = 0
    units = ['B', 'KB', 'MB', 'GB']
    value = float(n)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == 'B':
                return '%d B' % int(value)
            return '%.2f %s' % (value, unit)
        value /= 1024.0


def _cwd_root():
    return os.path.abspath(os.getcwd())


def _installer_root():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.abspath(os.getcwd())


def _explicit_root(path):
    if not path:
        raise SystemExit('Missing PATH argument.')
    path = os.path.expanduser(str(path))
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path


def _summary():
    total = sum(FILE_SIZES.values())
    lines = []
    lines.append('Pack: ' + PACK_NAME)
    lines.append('Files: %d' % len(FILES_B64))
    lines.append('Source size: ' + _format_bytes(total))
    lines.append('Default install root: current working directory')
    lines.append('Current working directory: ' + _cwd_root())
    lines.append('Installer directory: ' + _installer_root())
    return '\\n'.join(lines)


def list_files():
    print(_summary())
    print('')
    print('FILES:')
    for rel in sorted(FILES_B64):
        print('  %s  %s' % (_format_bytes(FILE_SIZES.get(rel, 0)), rel))


def dry_run(root=None):
    if root is None:
        root = _cwd_root()
    root = os.path.abspath(root)
    print(_summary())
    print('')
    print('DRY RUN: would write %d files to %s' % (len(FILES_B64), root))
    for rel in sorted(FILES_B64)[:80]:
        print('  would write: ' + rel)
    if len(FILES_B64) > 80:
        print('  ... %d more' % (len(FILES_B64) - 80))


def install(root=None):
    if root is None:
        root = _cwd_root()
    root = os.path.abspath(root)
    written = 0

    for rel, encoded in sorted(FILES_B64.items()):
        abs_path = os.path.abspath(os.path.join(root, rel))
        try:
            common = os.path.commonpath([root, abs_path])
        except Exception:
            common = ''
        if common != root:
            raise RuntimeError('Refusing to write outside install root: ' + rel)

        parent = os.path.dirname(abs_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(_decode(encoded))

        print('  wrote: ' + rel)
        written += 1

    print('')
    print('Done. %d files written to: %s' % (written, root))


def help_text():
    print(__doc__.strip())
    print('')
    print(_summary())


def _need_arg(argv, index, label):
    try:
        return argv[index]
    except Exception:
        raise SystemExit('Missing %s argument.' % label)


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    cmd = argv[0] if argv else '--install'

    if cmd in ('--help', 'help', '-h'):
        help_text()
        return 0

    if cmd in ('--list', 'list'):
        list_files()
        return 0

    if cmd in ('--dry-run', 'dry-run', 'preview'):
        root = _explicit_root(argv[1]) if len(argv) > 1 else _cwd_root()
        dry_run(root)
        return 0

    if cmd in ('--dry-run-here', 'dry-run-here', 'preview-here'):
        dry_run(_installer_root())
        return 0

    if cmd in ('--dry-run-root', 'dry-run-root', 'preview-root'):
        dry_run(_explicit_root(_need_arg(argv, 1, 'PATH')))
        return 0

    if cmd in ('--install', 'install'):
        root = _explicit_root(argv[1]) if len(argv) > 1 else _cwd_root()
        install(root)
        return 0

    if cmd in ('--install-here', 'install-here'):
        install(_installer_root())
        return 0

    if cmd in ('--install-root', 'install-root'):
        install(_explicit_root(_need_arg(argv, 1, 'PATH')))
        return 0

    print('Unknown argument: ' + str(cmd))
    print('Use --help, --list, --dry-run, --dry-run-here, --dry-run-root PATH, --install, --install-here, or --install-root PATH.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
'''

    return (
        template
        .replace('@@OUT_NAME@@', out_name)
        .replace('@@PACK_NAME@@', repr(out_name))
        .replace('@@PAYLOAD@@', payload)
        .replace('@@META_PAYLOAD@@', meta_payload)
    )


def _build_launcher(out_name, payload_filename):
    template = '''# -*- coding: utf-8 -*-
"""
run_@@OUT_NAME@@.py
===================

Tiny launcher for a large Forge PACK payload.

Open and run this file. Do not open the DO_NOT_OPEN payload file directly
in Pythonista's editor.
"""

import os
import runpy
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    payload = os.path.join(here, @@PAYLOAD_FILENAME@@)

    if not os.path.exists(payload):
        print("Missing payload:")
        print(payload)
        return 1

    old_argv = sys.argv[:]
    try:
        sys.argv = [payload] + old_argv[1:]
        runpy.run_path(payload, run_name="__main__")
        return 0
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return (
        template
        .replace('@@OUT_NAME@@', out_name)
        .replace('@@PAYLOAD_FILENAME@@', repr(payload_filename))
    )


def _pack_report(out_name, files_meta, out_rel='', installer_size=None, missing=None, skipped=None, warnings=None, dry_run=False, mode='script', launcher_rel='', payload_rel='', payload_size=None):
    missing = missing or []
    skipped = skipped or []
    warnings = warnings or []

    total_source_bytes = sum(int(item.get('bytes') or 0) for item in files_meta)

    lines = []
    lines.append('PACK REPORT')
    lines.append('===========')
    lines.append('')
    lines.append('name: %s' % out_name)
    lines.append('pack_mode: %s' % mode)
    lines.append('mode: %s' % ('dry-run' if dry_run else 'write'))
    if out_rel:
        lines.append('output: %s' % out_rel)
    if launcher_rel:
        lines.append('launcher: %s' % launcher_rel)
    if payload_rel:
        lines.append('payload: %s' % payload_rel)
    if installer_size is not None:
        lines.append('installer_size: %s' % _format_bytes(installer_size))
    if payload_size is not None:
        lines.append('payload_size: %s' % _format_bytes(payload_size))
    lines.append('files: %d' % len(files_meta))
    lines.append('source_size: %s' % _format_bytes(total_source_bytes))
    lines.append('missing: %d' % len(missing))
    lines.append('skipped: %d' % len(skipped))
    lines.append('warnings: %d' % len(warnings))
    lines.append('')

    if mode == 'folder':
        lines.append('FOLDER MODE')
        lines.append('- Run the launcher, not the payload.')
        if launcher_rel:
            lines.append('- Safe launcher: %s' % launcher_rel)
        if payload_rel:
            lines.append('- Large payload: %s' % payload_rel)
        lines.append('')

    lines.append('LARGEST FILES')
    if files_meta:
        for item in sorted(files_meta, key=lambda x: x.get('bytes') or 0, reverse=True)[:10]:
            lines.append('- %s  %s' % (_format_bytes(item.get('bytes') or 0), item.get('rel')))
    else:
        lines.append('- none')
    lines.append('')

    if warnings:
        lines.append('WARNINGS')
        for item in warnings[:20]:
            lines.append('- ' + item)
        if len(warnings) > 20:
            lines.append('- ... %d more' % (len(warnings) - 20))
        lines.append('')

    if missing:
        lines.append('MISSING INCLUDE PATHS')
        for path, reason in missing[:20]:
            lines.append('- %s (%s)' % (path, reason))
        if len(missing) > 20:
            lines.append('- ... %d more' % (len(missing) - 20))
        lines.append('')

    if skipped:
        lines.append('SKIPPED READ ERRORS')
        for item in skipped[:20]:
            lines.append('- ' + item)
        if len(skipped) > 20:
            lines.append('- ... %d more' % (len(skipped) - 20))
        lines.append('')

    lines.append('INSTALLER USAGE')
    if mode == 'folder' and launcher_rel:
        name = os.path.basename(launcher_rel)
        lines.append('- python %s --help' % name)
        lines.append('- python %s --list' % name)
        lines.append('- python %s --dry-run' % name)
        lines.append('- python %s --install' % name)
        lines.append('- python %s --install-here' % name)
        lines.append('- python %s --install-root PATH' % name)
    else:
        lines.append('- python %s.py --help' % out_name)
        lines.append('- python %s.py --list' % out_name)
        lines.append('- python %s.py --dry-run' % out_name)
        lines.append('- python %s.py --dry-run-here' % out_name)
        lines.append('- python %s.py --dry-run-root PATH' % out_name)
        lines.append('- python %s.py --install' % out_name)
        lines.append('- python %s.py --install-here' % out_name)
        lines.append('- python %s.py --install-root PATH' % out_name)

    return '\n'.join(lines).rstrip()


def execute(ctx, parsed_op, result):
    root = _project_root(ctx)
    directives = _directives(parsed_op)

    out_name = _safe_name(parsed_op.get('target') or '')
    include_paths = [
        line.strip()
        for line in (parsed_op.get('body') or '').splitlines()
        if line.strip()
    ]

    excludes = _parse_excludes(parsed_op)
    exts = _parse_ext(parsed_op)
    dry_run = _truthy(directives.get('DRY_RUN'))

    mode = str(directives.get('MODE') or 'script').strip().lower()
    if mode in ('', 'default'):
        mode = 'script'
    if mode not in ('script', 'folder'):
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'PACK MODE must be script or folder'
        return

    rels, missing = _collect_files(root, include_paths, excludes, exts)

    files_dict = {}
    files_meta = []
    skipped = []
    warnings = []

    for rel in rels:
        abs_path = os.path.join(root, rel)
        if _is_secret_like(rel):
            warnings.append('secret-like path included: ' + rel)

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            skipped.append('%s: %s: %s' % (rel, type(e).__name__, e))
            continue

        files_dict[rel] = content
        try:
            size = os.path.getsize(abs_path)
        except Exception:
            size = len(content.encode('utf-8', errors='replace'))
        files_meta.append({'rel': rel, 'bytes': size})

    if not files_dict and not missing:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'PACK found no files to include'
        return

    installer = _build_installer(files_dict, out_name, files_meta)
    packed_root = _packed_root(root)

    if mode == 'folder':
        payload_filename = 'DO_NOT_OPEN_%s_payload.py' % out_name
        launcher_filename = 'run_%s.py' % out_name
        folder_abs = os.path.join(packed_root, out_name)
        folder_rel = _rel_from_root(root, folder_abs)
        payload_abs = os.path.join(folder_abs, payload_filename)
        launcher_abs = os.path.join(folder_abs, launcher_filename)
        payload_rel = _rel_from_root(root, payload_abs)
        launcher_rel = _rel_from_root(root, launcher_abs)
        launcher = _build_launcher(out_name, payload_filename)

        report = _pack_report(
            out_name,
            files_meta,
            out_rel=folder_rel,
            installer_size=len(launcher.encode('utf-8')),
            payload_size=len(installer.encode('utf-8')),
            missing=missing,
            skipped=skipped,
            warnings=warnings,
            dry_run=dry_run,
            mode=mode,
            launcher_rel=launcher_rel,
            payload_rel=payload_rel,
        )

        if dry_run:
            result['status'] = 'APPLIED'
            result['message'] = 'PACK dry-run: %d file(s)' % len(files_meta)
            result['preview'] = report
            result['data'] = {
                'mode': mode,
                'dry_run': True,
                'files': files_meta,
                'missing': missing,
                'warnings': warnings,
                'skipped': skipped,
            }
            return

        if not os.path.isdir(folder_abs):
            os.makedirs(folder_abs)

        with open(payload_abs, 'w', encoding='utf-8') as f:
            f.write(installer)
        with open(launcher_abs, 'w', encoding='utf-8') as f:
            f.write(launcher)

        result['status'] = 'APPLIED'
        result['message'] = 'PACK wrote folder: ' + folder_rel
        result['file'] = launcher_rel
        result['folder'] = folder_rel
        result['payload'] = payload_rel
        result['preview'] = report
        result['data'] = {
            'mode': mode,
            'dry_run': False,
            'folder': folder_rel,
            'launcher': launcher_rel,
            'payload': payload_rel,
            'files': files_meta,
            'missing': missing,
            'warnings': warnings,
            'skipped': skipped,
        }
        result['touched'] = [
            {
                'rel': launcher_rel,
                'before': '',
                'after': launcher,
                'existed_before': False,
                'kind': 'file',
            },
            {
                'rel': payload_rel,
                'before': '',
                'after': installer,
                'existed_before': False,
                'kind': 'file',
            },
        ]
        return

    out_abs = os.path.join(packed_root, '%s.py' % out_name)
    out_rel = _rel_from_root(root, out_abs)

    report = _pack_report(
        out_name,
        files_meta,
        out_rel=out_rel,
        installer_size=len(installer.encode('utf-8')),
        missing=missing,
        skipped=skipped,
        warnings=warnings,
        dry_run=dry_run,
        mode=mode,
    )

    if dry_run:
        result['status'] = 'APPLIED'
        result['message'] = 'PACK dry-run: %d file(s)' % len(files_meta)
        result['preview'] = report
        result['data'] = {
            'mode': mode,
            'dry_run': True,
            'output': out_rel,
            'files': files_meta,
            'missing': missing,
            'warnings': warnings,
            'skipped': skipped,
        }
        return

    parent = os.path.dirname(out_abs)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    existed_before = os.path.exists(out_abs)
    before = ''
    if existed_before and os.path.isfile(out_abs):
        with open(out_abs, 'r', encoding='utf-8', errors='replace') as f:
            before = f.read()

    with open(out_abs, 'w', encoding='utf-8') as f:
        f.write(installer)

    result['status'] = 'APPLIED'
    result['message'] = 'PACK wrote installer: ' + out_rel
    result['file'] = out_rel
    result['preview'] = report
    result['data'] = {
        'mode': mode,
        'dry_run': False,
        'output': out_rel,
        'files': files_meta,
        'missing': missing,
        'warnings': warnings,
        'skipped': skipped,
    }
    result['touched'] = [{
        'rel': out_rel,
        'before': before,
        'after': installer,
        'existed_before': bool(existed_before),
        'kind': 'file',
    }]