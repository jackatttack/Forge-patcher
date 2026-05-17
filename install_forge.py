# -*- coding: utf-8 -*-
"""
install_forge.py
================

One-file public installer for Forge on Pythonista.

Usage:
1. Create a new Pythonista file named install_forge.py.
2. Paste this script into it.
3. Run it.

The installer downloads the public GitHub repo zip, extracts it, and installs
the repo's forge/ folder into Pythonista Documents.

Default install folder:

    ~/Documents/forge

Existing installs are backed up before replacement.
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


REPO_ZIP_URL = 'https://github.com/jackatttack/Forge-patcher/archive/refs/heads/main.zip'
INSTALL_DIR_NAME = 'forge'


def _documents_root():
    return os.path.abspath(os.path.expanduser('~/Documents'))


def _stamp():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


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
        and os.path.isfile(os.path.join(path, 'forge_entry.py'))
        and os.path.isfile(os.path.join(path, 'AI_FIRST_BOOT.txt'))
        and os.path.isfile(os.path.join(path, 'AI_MINIMAL_BOOT.txt'))
        and os.path.isdir(os.path.join(path, 'forge_core'))
        and os.path.isdir(os.path.join(path, 'forge_packages'))
    )


def _find_forge_folder(extract_dir):
    candidates = []

    for root, dirs, files in os.walk(extract_dir):
        if _is_forge_folder(root):
            candidates.append(root)

    if not candidates:
        raise RuntimeError('Could not find forge/ folder in downloaded repo.')

    candidates.sort(key=lambda p: (len(p), p))
    return candidates[0]


def install():
    docs = _documents_root()
    install_dir = os.path.join(docs, INSTALL_DIR_NAME)
    archive_dir = os.path.join(docs, 'archive')
    backup_dir = os.path.join(archive_dir, 'forge_before_install_' + _stamp())

    print('=== FORGE INSTALLER ===')
    print('Documents:', docs)
    print('Install folder:', install_dir)
    print('')

    tmp = tempfile.mkdtemp(prefix='forge_install_')
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
            print('Existing forge install found.')
            print('Backing up to:', backup_dir)
            if os.path.exists(backup_dir):
                _remove_tree(backup_dir)
            shutil.move(install_dir, backup_dir)

        print('')
        print('Installing...')
        _copy_tree(source_forge, install_dir)

        print('')
        print('Install complete.')
        print('')
        print('Next steps:')
        print('1. Open this file in Pythonista:')
        print('   forge/forge_entry.py')
        print('2. Run it once.')
        print('3. Copy one of these into a fresh AI chat:')
        print('   forge/AI_FIRST_BOOT.txt')
        print('   forge/AI_MINIMAL_BOOT.txt')
        print('')
        print('Optional later:')
        print('Run forge/install_root_router.py if you want a root Shortcut target:')
        print('   pythonista3://forge_entry.py?action=run')
        print('')

        return True

    except Exception as e:
        print('')
        print('INSTALL FAILED')
        print(type(e).__name__ + ': ' + str(e))
        return False

    finally:
        try:
            _remove_tree(tmp)
        except Exception:
            pass


if __name__ == '__main__':
    ok = install()
    if not ok:
        sys.exit(1)
