# -*- coding: utf-8 -*-
"""
ops.pip_op
==========
Install or uninstall a pure-Python package from PyPI.
Downloads a none-any wheel, extracts to site-packages,
verifies via import, and registers in .pypi_packages.
"""

import os
import json
import zipfile
import importlib
import configparser
import shutil
from urllib import request

SPEC = {
    'name': 'PIP',
    'target_kind': 'package',
    'body_mode': 'forbidden',
    'allowed_directives': {'ACTION', 'IMPORT', 'VERSION', 'CONFIRM'},
    'required_directives': {'ACTION'},
}

HELP = {
    'summary': 'Install or uninstall a pure-Python package from PyPI.',
    'subject': ['Package name as it appears on PyPI (e.g. chardet, httpx).'],
    'common_failures': [
        'No pure-Python wheel available - package requires compiled extensions.',
        'Network unreachable.',
        'Package not found on PyPI.',
        'IMPORT name differs from package name - use IMPORT: directive (e.g. beautifulsoup4 -> bs4).',
        'ACTION: uninstall requires CONFIRM: yes.',
    ],
    'safe_usage': [
        'Install verifies success via import after extraction.',
        'Already-importable packages are skipped with SKIPPED_ALREADY_PRESENT.',
        'Uninstall uses .pypi_packages registry, falls back to site-packages lookup.',
    ],
    'minimal_example': [
        'PIP chardet',
        'ACTION: install',
        '',
        'PIP chardet',
        'ACTION: uninstall',
        'CONFIRM: yes',
    ],
    'related_ops': ['RUN_FILE', 'READ_FILE'],
}

TMP_WHEEL = os.path.join(
    os.path.expanduser('~/Documents'),
    '_forge_pip_tmp.whl'

)


def validate(parsed_op):
    errors = []
    if not (parsed_op.target or '').strip():
        errors.append('PIP requires a package name as target')
    action = (parsed_op.directives.get('ACTION') or '').lower()
    if action not in ('install', 'uninstall'):
        errors.append('ACTION must be: install | uninstall')
    if action == 'uninstall':
        if (parsed_op.directives.get('CONFIRM') or '').lower() != 'yes':
            errors.append('ACTION: uninstall requires CONFIRM: yes')
    return errors


def execute(ctx, parsed_op, result):
    action = parsed_op.directives.get('ACTION', '').lower()
    package = parsed_op.target.strip()
    import_name = (parsed_op.directives.get('IMPORT') or package).strip()

    sp = os.path.join(ctx.project_root, 'site-packages')
    pypi_db = os.path.join(sp, '.pypi_packages')

    if action == 'install':
        _install(result, package, import_name, sp, pypi_db)
    else:
        _uninstall(result, package, import_name, sp, pypi_db)


def _install(result, package, import_name, sp, pypi_db):
    # Already importable?
    importlib.invalidate_caches()
    try:
        importlib.import_module(import_name)
        result['status'] = 'SKIPPED_ALREADY_PRESENT'
        result['message'] = f"'{import_name}' is already importable"
        return
    except ImportError:
        pass

    # Fetch PyPI metadata
    try:
        with request.urlopen(f'https://pypi.org/pypi/{package}/json', timeout=15) as r:
            meta = json.loads(r.read().decode())
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = f'PyPI fetch failed: {e}'
        return

    info = meta['info']
    version = info['version']
    summary = info.get('summary', '')

    # Find pure-python wheel
    wheel = None
    for f in meta.get('urls', []):
        if f['filename'].endswith('.whl') and 'none-any' in f['filename']:
            wheel = f
            break

    if not wheel:
        result['status'] = 'FAILED_IO'
        result['message'] = (
            f"No pure-Python wheel for '{package}' {version}. "
            f"Package may require compiled extensions."
        )
        return

    # Download
    try:
        with request.urlopen(wheel['url'], timeout=30) as r:
            data = r.read()
        with open(TMP_WHEEL, 'wb') as f:
            f.write(data)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = f'Download failed: {e}'
        return

    # Extract (skip .dist-info)
    installed = []
    try:
        with zipfile.ZipFile(TMP_WHEEL) as zf:
            for name in zf.namelist():
                if '.dist-info/' in name:
                    continue
                dest = os.path.join(sp, name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zf.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
                installed.append(dest)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = f'Extraction failed: {e}'
        return
    finally:
        if os.path.exists(TMP_WHEEL):
            os.remove(TMP_WHEEL)

    # Verify import
    importlib.invalidate_caches()
    try:
        importlib.import_module(import_name)
    except ImportError as e:
        result['status'] = 'FAILED_INSTALL'
        result['message'] = f'Extracted but import failed: {e}'
        return

    # Register in .pypi_packages
    cfg = configparser.ConfigParser()
    if os.path.exists(pypi_db):
        cfg.read(pypi_db, encoding='utf-8')
    cfg[package] = {
        'url': 'pypi',
        'version': version,
        'summary': summary,
        'files': ','.join(installed),
        'dependency': '',
    }
    with open(pypi_db, 'w', encoding='utf-8') as f:
        cfg.write(f)

    result['status'] = 'APPLIED'
    result['message'] = f"Installed '{package}' {version} ({len(installed)} files)"


def _uninstall(result, package, import_name, sp, pypi_db):
    cfg = configparser.ConfigParser()
    if os.path.exists(pypi_db):
        cfg.read(pypi_db, encoding='utf-8')

    section = next((s for s in cfg.sections() if s.lower() == package.lower()), None)

    removed = []
    if section:
        files_str = cfg[section].get('files', '')
        for raw in files_str.split(','):
            raw = raw.strip()
            if not raw:
                continue
            if 'site-packages/' in raw:
                rel = raw.split('site-packages/', 1)[1]
                abs_path = os.path.join(sp, rel)
            else:
                abs_path = raw

            if os.path.isfile(abs_path):
                os.remove(abs_path)
                removed.append(abs_path)
            elif os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
                removed.append(abs_path)

        cfg.remove_section(section)
        with open(pypi_db, 'w', encoding='utf-8') as f:
            cfg.write(f)

    else:
        pkg_dir = os.path.join(sp, import_name)
        pkg_file = os.path.join(sp, import_name + '.py')
        if os.path.isdir(pkg_dir):
            shutil.rmtree(pkg_dir)
            removed.append(pkg_dir)
        elif os.path.isfile(pkg_file):
            os.remove(pkg_file)
            removed.append(pkg_file)
        else:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = f"'{package}' not found in .pypi_packages or site-packages"
            return

    # Evict from module cache so same-session import checks reflect reality
    import sys
    sys.modules.pop(import_name, None)

    result['status'] = 'APPLIED'
    result['message'] = f"Uninstalled '{package}' ({len(removed)} items removed)"
