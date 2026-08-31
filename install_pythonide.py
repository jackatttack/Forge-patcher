# -*- coding: utf-8 -*-
"""
install_pythonide.py
====================

One-file Forge installer for the "Python IDE" iOS app.

Installs the public Forge release into the app's writable Workspace and creates
a root-level forge_entry.py launcher that uses Python IDE's clipboard module.

Typical result:

    Workspace/
        forge/
        forge_entry.py

Run afterward:

    python3 forge_entry.py
"""

from __future__ import print_function

import datetime
import os
import shutil
import sys
import tempfile
import zipfile

try:
    from urllib.request import urlopen
except Exception:
    from urllib2 import urlopen


REPO_ZIP_URL = (
    'https://github.com/'
    'jackatttack/Forge-patcher/archive/refs/heads/main.zip'
)

INSTALL_DIR_NAME = 'forge'
ROOT_ENTRY_NAME = 'forge_entry.py'


ROOT_ENTRY_SOURCE = r'''# -*- coding: utf-8 -*-
"""Stable root launcher for Forge inside Python IDE."""

from __future__ import print_function

import os
import runpy

HERE = os.path.abspath(os.path.dirname(__file__))
ENTRY = os.path.join(HERE, 'forge', 'pythonide_entry.py')

if not os.path.isfile(ENTRY):
    raise RuntimeError('Forge Python IDE entry point is missing: ' + ENTRY)

runpy.run_path(ENTRY, run_name='__main__')
'''


def _stamp():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def _existing_dir(value):
    value = str(value or '').strip()
    if not value:
        return ''

    path = os.path.abspath(os.path.expanduser(value))
    if os.path.isdir(path):
        return path

    return ''


def _workspace_root():
    """Find Python IDE's writable Workspace without using ~/Documents."""
    candidates = [
        os.environ.get('PY_WORKSPACE'),
        os.environ.get('WORKSPACE'),
        os.getcwd(),
    ]

    try:
        candidates.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass

    seen = set()

    for candidate in candidates:
        path = _existing_dir(candidate)
        if not path or path in seen:
            continue
        seen.add(path)

        if os.access(path, os.W_OK):
            return path

    raise RuntimeError(
        'Could not find a writable Python IDE Workspace. '
        'Run this installer from the Workspace directory.'
    )


def _ensure_dir(path):
    if path and not os.path.isdir(path):
        os.makedirs(path)


def _remove_tree(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


def _copy_tree(src, dst):
    if os.path.exists(dst):
        raise RuntimeError('Destination already exists: ' + dst)
    shutil.copytree(src, dst)


def _download(url, dest):
    print('Downloading Forge...')
    print(url)

    data = urlopen(url, timeout=60).read()

    with open(dest, 'wb') as f:
        f.write(data)

    print('Downloaded: %.2f KB' % (len(data) / 1024.0))


def _is_forge_folder(path):
    return (
        os.path.isdir(path)
        and os.path.isfile(os.path.join(path, 'entry.py'))
        and os.path.isfile(os.path.join(path, 'forge_entry.py'))
        and os.path.isfile(os.path.join(path, 'pythonide_entry.py'))
        and os.path.isdir(os.path.join(path, 'forge_core'))
        and os.path.isdir(os.path.join(path, 'forge_packages'))
    )


def _find_forge_folder(extract_dir):
    candidates = []

    for root, dirs, files in os.walk(extract_dir):
        if _is_forge_folder(root):
            candidates.append(root)

    if not candidates:
        raise RuntimeError(
            'Could not find a Python IDE-capable forge/ folder '
            'in the downloaded repository.'
        )

    candidates.sort(key=lambda p: (len(p), p))
    return candidates[0]


def _write_root_entry(path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(ROOT_ENTRY_SOURCE)


def _clipboard_probe():
    try:
        import clipboard
        before = clipboard.get()

        marker = 'FORGE_PYTHONIDE_INSTALL_PROBE'
        clipboard.set(marker)
        after = clipboard.get()

        if after != marker:
            return False, 'clipboard round-trip mismatch'

        try:
            clipboard.set('' if before is None else str(before))
        except Exception:
            pass

        return True, ''

    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)


def _smoke_import(workspace, install_dir):
    os.environ['FORGE_HOME'] = install_dir
    os.environ['FORGE_PROJECT_ROOT'] = workspace

    if install_dir not in sys.path:
        sys.path.insert(0, install_dir)

    import importlib.util

    entry_path = os.path.join(install_dir, 'entry.py')
    spec = importlib.util.spec_from_file_location(
        'forge_pythonide_install_smoke',
        entry_path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError('Could not import installed Forge entry.py')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    run = module.run_from_text(
        'HELP REPLACE full\n',
        project_root=workspace,
        mode='test',
        store=False,
    )

    packet = str((run or {}).get('packet') or '')
    if 'HELP REPLACE' not in packet:
        raise RuntimeError('Forge smoke test did not return HELP REPLACE output')


def install():
    workspace = _workspace_root()
    install_dir = os.path.join(workspace, INSTALL_DIR_NAME)
    root_entry = os.path.join(workspace, ROOT_ENTRY_NAME)
    archive_dir = os.path.join(workspace, 'archive')

    stamp = _stamp()
    backup_dir = os.path.join(
        archive_dir,
        'forge_before_pythonide_install_' + stamp,
    )
    entry_backup = os.path.join(
        archive_dir,
        'forge_entry_before_pythonide_install_' + stamp + '.py',
    )

    print('=== FORGE / PYTHON IDE INSTALLER ===')
    print('Workspace:', workspace)
    print('Forge:', install_dir)
    print('Entry point:', root_entry)
    print('')

    clipboard_ok, clipboard_error = _clipboard_probe()
    if not clipboard_ok:
        raise RuntimeError(
            'Clipboard access is required for Forge: ' + clipboard_error
        )

    print('Clipboard round-trip: PASS')

    tmp = tempfile.mkdtemp(prefix='forge_pythonide_install_')
    zip_path = os.path.join(tmp, 'forge_main.zip')
    extract_dir = os.path.join(tmp, 'extract')
    _ensure_dir(extract_dir)

    try:
        _download(REPO_ZIP_URL, zip_path)

        print('')
        print('Extracting...')

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)

        source_forge = _find_forge_folder(extract_dir)
        print('Found Forge folder:', source_forge)

        if os.path.exists(install_dir):
            _ensure_dir(archive_dir)

            print('')
            print('Existing Forge install found.')
            print('Backing up to:', backup_dir)

            if os.path.exists(backup_dir):
                _remove_tree(backup_dir)

            shutil.move(install_dir, backup_dir)

        if os.path.isfile(root_entry):
            _ensure_dir(archive_dir)
            print('Backing up existing root entry to:', entry_backup)
            shutil.copy2(root_entry, entry_backup)

        print('')
        print('Installing Forge...')
        _copy_tree(source_forge, install_dir)

        print('Writing root entry...')
        _write_root_entry(root_entry)

        print('Running non-mutating smoke test...')
        _smoke_import(workspace, install_dir)

        print('')
        print('INSTALL COMPLETE')
        print('')
        print('Forge is installed for Python IDE.')
        print('')
        print('Normal loop:')
        print('1. Copy a Forge bundle from ChatGPT.')
        print('2. Run:')
        print('      python3 forge_entry.py')
        print('3. Forge runs against this Workspace.')
        print('4. The Forge return packet is copied to the clipboard.')
        print('5. Paste it back into ChatGPT.')
        print('')
        print('AI boot prompts:')
        print('   forge/AI_FIRST_BOOT.txt')
        print('   forge/AI_MINIMAL_BOOT.txt')
        print('')

        return True

    except Exception:
        if (
            not os.path.exists(install_dir)
            and os.path.isdir(backup_dir)
        ):
            try:
                shutil.move(backup_dir, install_dir)
            except Exception:
                pass
        raise

    finally:
        try:
            _remove_tree(tmp)
        except Exception:
            pass


if __name__ == '__main__':
    try:
        ok = install()
    except Exception as e:
        print('')
        print('INSTALL FAILED')
        print(type(e).__name__ + ': ' + str(e))
        sys.exit(1)

    sys.exit(0 if ok else 1)
