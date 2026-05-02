# -*- coding: utf-8 -*-
"""
ops.pack
========
Pack a set of files into a portable self-installing Python script.

Usage:
    PACK my_backup
    EXCLUDE: forge/forge_runs/, forge/forge_app/
    EXT: *
    BEGIN_BODY
    forge/
    forge_entry.py
    END_BODY

Output: forge/artifacts/packed/my_backup.py — portable installer. By default it restores files to the current working directory.
"""

import os

# Absolute path to Pythonista Documents folder at pack-generation time.
# This is stored as metadata only in generated installers; it is not used as
# the default install target.
DOCUMENTS_ROOT = '/private/var/mobile/Containers/Shared/AppGroup/2BDBE521-A867-4CC9-932E-BB723BB7DBAC/Pythonista3/Documents'

SPEC = {
    'name': 'PACK',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': {'EXCLUDE', 'EXT', 'DRY_RUN', 'MODE'},
    'required_directives': set(),
    'summary': 'Pack files and directories into a self-installing Python script saved to forge/artifacts/packed/.',
}

HINTS = {
    'body required': 'List paths to include in the body — one file or directory per line',
    'target': 'Provide an output name e.g. PACK forge_backup (no extension needed)',
}

HELP = {
    'summary': 'Pack files and directories into a self-installing Python script saved to forge/artifacts/packed/.',
    'subject': ['Output filename without extension — saved to forge/artifacts/packed/<name>.py by default, or forge/artifacts/packed/<name>/ in folder mode'],
    'body': [
        'One include path per line.',
        'Directories are walked recursively.',
        'EXT controls which extensions are collected from dirs (default: all).',
        'DRY_RUN: yes previews the pack report without writing an installer.',
        'MODE: folder writes a large DO_NOT_OPEN payload plus a tiny run_<name>.py launcher.',
    ],
    'directives': {
        'EXCLUDE': 'Comma-separated skip patterns.',
        'EXT': 'Comma-separated file extensions, or * for all files.',
        'DRY_RUN': 'yes/no. Preview without writing output.',
        'MODE': 'script or folder. Default script preserves old forge/artifacts/packed/<name>.py behaviour.',
    },
    'common_failures': [
        'No paths in body.',
        'Include path not found.',
        'Target name missing.',
        'Secret-looking files included by accident.',
    ],
    'safe_usage': [
        'Generated installers default to current working directory, not the original device path.',
        'Use --install-here to write beside the installer file.',
        'Use --install-root PATH for an explicit install target.',
        'Generated installers support --help, --list, --dry-run, --dry-run-here, --dry-run-root PATH, --install, --install-here, and --install-root PATH.',
        'Use MODE: folder for large packs so Pythonista opens the tiny launcher instead of the huge payload.',
        'In folder mode, avoid opening DO_NOT_OPEN_<name>_payload.py directly in the Pythonista editor.',
        'Use EXCLUDE to skip run dirs, secrets, caches, and device-local files.',
        'Check the post-pack report for size, largest files, skipped files, and warnings.',
        'Combine dirs and individual files freely in the body.',
    ],
    'minimal_example': [
        'PACK forge_backup',
        'EXCLUDE: forge/forge_runs/, forge/forge_app/, .forge_secrets/, api_key, token',
        'BEGIN_BODY',
        'forge/',
        'forge_entry.py',
        'END_BODY',
        '',
        'PACK forge_backup_folder',
        'MODE: folder',
        'EXCLUDE: forge/forge_runs/, .forge_secrets/',
        'BEGIN_BODY',
        'forge/',
        'forge_entry.py',
        'END_BODY',
        '',
        'PACK forge_backup_check',
        'DRY_RUN: yes',
        'EXCLUDE: forge/forge_runs/, .forge_secrets/',
        'BEGIN_BODY',
        'forge/',
        'forge_entry.py',
        'END_BODY',
    ],
    'related_ops': ['COPY_FILE', 'CREATE_FILE', 'LIST_FILES', 'RUN_FILE'],
}


def validate(parsed_op):
    """Check target path is present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('PACK requires a target name')
    if not parsed_op.body or not parsed_op.body.strip():
        errors.append('PACK requires body content — list paths to include')
    return errors


def _parse_excludes(parsed_op):
    """Parse EXCLUDE directive into a list of path substrings to skip."""
    raw = parsed_op.directives.get('EXCLUDE', '')
    return [e.strip() for e in raw.split(',') if e.strip()]


def _parse_ext(parsed_op):
    """Parse EXT directive into a tuple of allowed file extensions."""
    raw = parsed_op.directives.get('EXT', '*').strip()
    if raw == '*':
        return None  # None means all extensions
    return [e.strip().lstrip('.') for e in raw.split(',') if e.strip()]


def _should_exclude(rel, excludes):
    """Return True if file path matches any exclude pattern or is a binary/cache type.

    EXCLUDE patterns are intentionally forgiving:
    - exact path match
    - prefix match for directories
    - substring match for secret tokens such as api_key, token, password
    """
    rel = rel or ''
    rel_l = rel.lower()

    for ex in excludes:
        ex = (ex or '').strip()
        if not ex:
            continue
        ex_l = ex.lower()
        if rel_l == ex_l or rel_l.startswith(ex_l) or ex_l in rel_l:
            return True

    if rel.endswith('.bak'):
        return True
    return False

def _collect_files(root, include_paths, excludes, exts):
    """Walk target directory and return list of (rel_path, abs_path) pairs to pack."""
    collected = []
    for path in include_paths:
        path = path.strip()
        if not path:
            continue
        abs_path = os.path.join(root, path)
        if os.path.isdir(abs_path):
            for dirpath, dirnames, filenames in os.walk(abs_path):
                dirnames[:] = sorted(
                    x for x in dirnames
                    if not x.startswith('.') and x != '__pycache__'
                )
                for fn in sorted(filenames):
                    if fn.startswith('.'):
                        continue
                    if exts is not None:
                        ext = fn.rsplit('.', 1)[-1] if '.' in fn else ''
                        if ext not in exts:
                            continue
                    file_abs = os.path.join(dirpath, fn)
                    rel = os.path.relpath(file_abs, root)
                    if not _should_exclude(rel, excludes):
                        collected.append(rel)
        elif os.path.isfile(abs_path):
            rel = os.path.relpath(abs_path, root)
            if not _should_exclude(rel, excludes):
                collected.append(rel)
        else:
            collected.append(('MISSING', path))
    return collected


def _format_bytes(n):
    """Return a compact human-readable byte size."""
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


def _is_yes(value):
    """Return True for common affirmative directive values."""
    return str(value or '').strip().lower() in ('1', 'yes', 'true', 'on')


def _is_secret_like(rel):
    """Best-effort warning for paths that should usually not be packed."""
    s = (rel or '').lower()
    risky_tokens = [
        'api_key',
        'apikey',
        'secret',
        'token',
        'password',
        'credential',
        'credentials',
        'private_key',
        'forge_key.json',
        '.forge_secrets',
    ]
    return any(tok in s for tok in risky_tokens)


def _pack_report(out_name, files_meta, out_rel=None, installer_size=None, missing=None, skipped=None, warnings=None, dry_run=False, mode='script', launcher_rel=None, payload_rel=None, payload_size=None):
    """Build the human-facing PACK report."""
    missing = missing or []
    skipped = skipped or []
    warnings = warnings or []

    total_source_bytes = sum(int(item.get('bytes') or 0) for item in files_meta)
    lines = []
    lines.append('=== PACK REPORT ===')
    lines.append('name: %s' % out_name)
    lines.append('pack_mode: %s' % (mode or 'script'))
    if out_rel:
        lines.append('installer: %s' % out_rel)
    if launcher_rel:
        lines.append('launcher: %s' % launcher_rel)
    if payload_rel:
        lines.append('payload: %s' % payload_rel)
    if installer_size is not None:
        lines.append('installer_size: %s' % _format_bytes(installer_size))
    if payload_size is not None:
        lines.append('payload_size: %s' % _format_bytes(payload_size))
    lines.append('mode: %s' % ('dry-run' if dry_run else 'write'))
    lines.append('files: %d' % len(files_meta))
    lines.append('source_size: %s' % _format_bytes(total_source_bytes))
    lines.append('missing: %d' % len(missing))
    lines.append('skipped: %d' % len(skipped))
    lines.append('warnings: %d' % len(warnings))
    lines.append('')

    if mode == 'folder':
        lines.append('FOLDER MODE:')
        lines.append('- Open/run the launcher, not the payload.')
        if launcher_rel:
            lines.append('- Safe launcher: %s' % launcher_rel)
        if payload_rel:
            lines.append('- Large payload: %s' % payload_rel)
        lines.append('- Payload filename is deliberately marked DO_NOT_OPEN to avoid Pythonista editor crashes.')
        lines.append('')

    lines.append('LARGEST FILES:')
    if files_meta:
        for item in sorted(files_meta, key=lambda x: x.get('bytes') or 0, reverse=True)[:10]:
            lines.append('- %s  %s' % (_format_bytes(item.get('bytes') or 0), item.get('rel')))
    else:
        lines.append('- none')
    lines.append('')

    if warnings:
        lines.append('WARNINGS:')
        for item in warnings[:20]:
            lines.append('- ' + item)
        if len(warnings) > 20:
            lines.append('- ... %d more' % (len(warnings) - 20))
        lines.append('')

    if missing:
        lines.append('MISSING INCLUDE PATHS:')
        for _, path in missing[:20]:
            lines.append('- ' + path)
        if len(missing) > 20:
            lines.append('- ... %d more' % (len(missing) - 20))
        lines.append('')

    if skipped:
        lines.append('SKIPPED READ ERRORS:')
        for item in skipped[:20]:
            lines.append('- ' + item)
        if len(skipped) > 20:
            lines.append('- ... %d more' % (len(skipped) - 20))
        lines.append('')

    lines.append('INSTALLER USAGE:')
    if mode == 'folder' and launcher_rel:
        launcher_name = os.path.basename(launcher_rel)
        lines.append('- python %s --help' % launcher_name)
        lines.append('- python %s --list' % launcher_name)
        lines.append('- python %s --dry-run' % launcher_name)
        lines.append('- python %s --install' % launcher_name)
        lines.append('- python %s --install-here' % launcher_name)
        lines.append('- python %s --install-root PATH' % launcher_name)
    else:
        lines.append('- python %s.py --help' % out_name)
        lines.append('- python %s.py --list' % out_name)
        lines.append('- python %s.py --dry-run          # preview install to current working directory' % out_name)
        lines.append('- python %s.py --dry-run-here     # preview install beside the installer file' % out_name)
        lines.append('- python %s.py --dry-run-root PATH # preview install to explicit path' % out_name)
        lines.append('- python %s.py --install          # install to current working directory' % out_name)
        lines.append('- python %s.py --install-here     # install beside the installer file' % out_name)
        lines.append('- python %s.py --install-root PATH # install to explicit path' % out_name)
    return '\n'.join(lines)

def _build_installer(files_dict, out_name, files_meta=None):
    """Build a portable self-installing Python script that recreates packed files.

    Important portability rule:
    - The generated installer must not use the original device's project root as
      its default install target.
    - Default install target is current working directory.
    - --install-here installs relative to the installer file location.
    - --install-root PATH allows explicit override.
    """
    import base64

    entries = []
    for rel, content in sorted(files_dict.items()):
        data = base64.b64encode((content or '').encode('utf-8')).decode('ascii')
        entries.append('    %r: %r,' % (rel, data))
    payload = '\n'.join(entries)

    meta_entries = []
    for item in sorted(files_meta or [], key=lambda x: x.get('rel', '')):
        meta_entries.append('    %r: %r,' % (item.get('rel'), int(item.get('bytes') or 0)))
    meta_payload = '\n'.join(meta_entries)

    template = '''# -*- coding: utf-8 -*-
"""
@@OUT_NAME@@.py
==========
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
This is intentionally portable across Pythonista/iOS containers.
"""

import base64
import os
import sys

PACK_NAME = @@PACK_NAME@@
SOURCE_ROOT_AT_PACK_TIME = @@SOURCE_ROOT_AT_PACK_TIME@@

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
        here = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        here = os.getcwd()
    return os.path.abspath(here)


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
    lines.append('Source root at pack time: ' + SOURCE_ROOT_AT_PACK_TIME)
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
    for rel in sorted(FILES_B64)[:40]:
        print('  would write: ' + rel)
    if len(FILES_B64) > 40:
        print('  ... %d more' % (len(FILES_B64) - 40))


def install(root=None):
    if root is None:
        root = _cwd_root()
    root = os.path.abspath(root)
    written = 0

    for rel, encoded in FILES_B64.items():
        abs_path = os.path.abspath(os.path.join(root, rel))

        # Packed paths are generated by Forge and should be relative, but keep a
        # safety guard in the installer too.
        try:
            common = os.path.commonpath([root, abs_path])
        except Exception:
            common = ''
        if common != root:
            raise RuntimeError('Refusing to write outside install root: ' + rel)

        dir_path = os.path.dirname(abs_path)
        if dir_path and not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(_decode(encoded))
        print('  wrote: ' + rel)
        written += 1

    print('')
    print('Done. %d files written to: ' % written + root)


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
        .replace('@@SOURCE_ROOT_AT_PACK_TIME@@', repr(DOCUMENTS_ROOT))
        .replace('@@PAYLOAD@@', payload)
        .replace('@@META_PAYLOAD@@', meta_payload)
    )

def _build_launcher(out_name, payload_filename):
    """Build a tiny launcher that runs the large payload script beside it."""
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

def execute(ctx, parsed_op, result):
    """Collect files from target, build installer script, write to forge/artifacts/packed/ directory."""
    root = ctx.project_root
    target_name = (parsed_op.target or '').strip()
    out_name = target_name if not target_name.endswith('.py') else target_name[:-3]
    out_name = out_name.strip().strip('/')

    include_paths = [
        line.strip()
        for line in (parsed_op.body or '').splitlines()
        if line.strip()
    ]
    excludes = _parse_excludes(parsed_op)
    exts = _parse_ext(parsed_op)
    dry_run = _is_yes(parsed_op.directives.get('DRY_RUN'))

    pack_mode = (parsed_op.directives.get('MODE') or 'script').strip().lower()
    if pack_mode in ('', 'default'):
        pack_mode = 'script'
    if pack_mode not in ('script', 'folder'):
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'PACK MODE must be script or folder'
        return

    collected = _collect_files(root, include_paths, excludes, exts)

    missing = []
    skipped = []
    warnings = []
    files_dict = {}
    files_meta = []

    for item in collected:
        if isinstance(item, tuple) and item and item[0] == 'MISSING':
            missing.append(item)
            continue

        rel = item
        abs_path = os.path.join(root, rel)

        if _is_secret_like(rel):
            warnings.append('secret-like path included: ' + rel)

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            skipped.append('%s: %s' % (rel, e))
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

    packed_dir = os.path.join(root, 'forge', 'artifacts', 'packed')
    if not os.path.isdir(packed_dir):
        os.makedirs(packed_dir)

    if pack_mode == 'folder':
        folder_rel = 'forge/artifacts/packed/%s' % out_name
        folder_abs = os.path.join(root, folder_rel)
        payload_filename = 'DO_NOT_OPEN_%s_payload.py' % out_name
        launcher_filename = 'run_%s.py' % out_name

        payload_abs = os.path.join(folder_abs, payload_filename)
        launcher_abs = os.path.join(folder_abs, launcher_filename)
        payload_rel = '%s/%s' % (folder_rel, payload_filename)
        launcher_rel = '%s/%s' % (folder_rel, launcher_filename)

        launcher = _build_launcher(out_name, payload_filename)

        if dry_run:
            result['status'] = 'APPLIED'
            result['message'] = _pack_report(
                out_name,
                files_meta,
                out_rel=folder_rel,
                installer_size=len(launcher.encode('utf-8')),
                payload_size=len(installer.encode('utf-8')),
                missing=missing,
                skipped=skipped,
                warnings=warnings,
                dry_run=True,
                mode=pack_mode,
                launcher_rel=launcher_rel,
                payload_rel=payload_rel,
            )
            return

        if not os.path.isdir(folder_abs):
            os.makedirs(folder_abs)

        with open(payload_abs, 'w', encoding='utf-8') as f:
            f.write(installer)
        with open(launcher_abs, 'w', encoding='utf-8') as f:
            f.write(launcher)

        result['status'] = 'APPLIED'
        result['file'] = launcher_rel
        result['folder'] = folder_rel
        result['payload'] = payload_rel
        result['message'] = _pack_report(
            out_name,
            files_meta,
            out_rel=folder_rel,
            installer_size=os.path.getsize(launcher_abs),
            payload_size=os.path.getsize(payload_abs),
            missing=missing,
            skipped=skipped,
            warnings=warnings,
            dry_run=False,
            mode=pack_mode,
            launcher_rel=launcher_rel,
            payload_rel=payload_rel,
        )
        return

    out_rel = 'forge/artifacts/packed/%s.py' % out_name
    out_abs = os.path.join(root, out_rel)

    if dry_run:
        result['status'] = 'APPLIED'
        result['message'] = _pack_report(
            out_name,
            files_meta,
            out_rel=out_rel,
            installer_size=len(installer.encode('utf-8')),
            missing=missing,
            skipped=skipped,
            warnings=warnings,
            dry_run=True,
            mode=pack_mode,
        )
        return

    with open(out_abs, 'w', encoding='utf-8') as f:
        f.write(installer)

    result['status'] = 'APPLIED'
    result['file'] = out_rel
    result['message'] = _pack_report(
        out_name,
        files_meta,
        out_rel=out_rel,
        installer_size=os.path.getsize(out_abs),
        missing=missing,
        skipped=skipped,
        warnings=warnings,
        dry_run=False,
        mode=pack_mode,
    )
