# -*- coding: utf-8 -*-
"""
install_root_router.py
======================

Install or refresh the root-level Forge entry script.

This copies:

    forge/forge_entry.py

to:

    forge_entry.py

at the Pythonista Documents root.

Why this exists:
- the workspace contains the real Forge implementation
- the root file gives iOS Shortcuts and Pythonista URL links one stable target
- the root file reads the clipboard, runs Forge, copies the packet return, and renders the human Surface
"""

import os
import shutil
from datetime import datetime


ROOT = os.path.abspath(os.path.expanduser('~/Documents'))
FORGE_HOME = os.path.abspath(os.path.dirname(__file__))
SOURCE_REL = os.path.relpath(os.path.join(FORGE_HOME, 'forge_entry.py'), ROOT)
DEST_REL = 'forge_entry.py'
BACKUP_DIR = os.path.join(FORGE_HOME, 'artifacts', 'root_router_backups')


def _read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _ensure_dir(path):
    if path and not os.path.isdir(path):
        os.makedirs(path)


def _backup_existing(dest_abs):
    if not os.path.isfile(dest_abs):
        return ''

    backup_dir = BACKUP_DIR
    _ensure_dir(backup_dir)

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_abs = os.path.join(backup_dir, 'forge_entry_%s.py' % stamp)
    shutil.copy2(dest_abs, backup_abs)
    return backup_abs


def install():
    source_abs = os.path.join(FORGE_HOME, 'forge_entry.py')
    dest_abs = os.path.join(ROOT, DEST_REL)

    if not os.path.isfile(source_abs):
        raise RuntimeError('Missing source launcher: ' + SOURCE_REL)

    source_text = _read(source_abs)
    existing_text = _read(dest_abs) if os.path.isfile(dest_abs) else None

    if existing_text == source_text:
        print('Forge root router already up to date.')
        print('root: ' + DEST_REL)
        return 0

    backup_abs = _backup_existing(dest_abs)

    with open(dest_abs, 'w', encoding='utf-8') as f:
        f.write(source_text)

    print('Forge root router installed.')
    print('source: ' + SOURCE_REL)
    print('root: ' + DEST_REL)

    if backup_abs:
        print('backup: ' + os.path.relpath(backup_abs, ROOT))

    print('')
    print('Shortcut target:')
    print('pythonista3://forge_entry.py?action=run')
    print('')
    print('Loop:')
    print('1. Copy a Forge bundle to clipboard.')
    print('2. Run forge_entry.py.')
    print('3. Paste the returned packet back into chat.')

    return 0


if __name__ == '__main__':
    raise SystemExit(install())