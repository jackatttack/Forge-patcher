# -*- coding: utf-8 -*-
"""
PIP op.

Install or uninstall a pure-Python package from PyPI.

Downloads a none-any wheel, extracts to project site-packages, verifies via
import, and registers installed files in .pypi_packages.
"""

import configparser
import importlib
import json
import os
import shutil
import sys
import zipfile
from urllib import request


SPEC = {
    'name': 'PIP',
    'target_kind': 'package',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ACTION', 'IMPORT', 'VERSION', 'CONFIRM']),
    'required_directives': set(),
}


HELP = {
    'summary': 'Install or uninstall a pure-Python package from PyPI.',
    'subject': [
        'Package name as it appears on PyPI, e.g. chardet or beautifulsoup4.',
    ],
    'minimal_example': [
        'PIP install chardet',
        '',
        'PIP install beautifulsoup4',
        'IMPORT: bs4',
        '',
        'PIP uninstall chardet',
        'CONFIRM: yes',
        '',
        'PIP chardet',
        'ACTION: install',
    ],
    'common_failures': [
        'No pure-Python wheel is available.',
        'Package requires compiled extensions.',
        'Network unavailable.',
        'Package not found on PyPI.',
        'Import name differs from package name; use IMPORT.',
        'ACTION: uninstall requires CONFIRM: yes.',
    ],
    'safe_usage': [
        'Install verifies success via import after extraction.',
        'Already-importable packages are skipped with SKIPPED_ALREADY_PRESENT.',
        'Uninstall requires CONFIRM: yes.',
        'Use RUN_FILE after install to verify the package in a tiny script.',
    ],
}


HINTS = {
    '_max_hints': 1,
    'action': {
        'message': 'PIP needs ACTION: install or ACTION: uninstall.',
        'why': 'The op must know whether to add or remove a package.',
        'example': ['PIP chardet', 'ACTION: install'],
        'next': ['Add ACTION: install or ACTION: uninstall.'],
    },
    'confirm': {
        'message': 'PIP uninstall requires CONFIRM: yes.',
        'why': 'Uninstall mutates site-packages and should be deliberate.',
        'example': ['PIP chardet', 'ACTION: uninstall', 'CONFIRM: yes'],
        'next': ['Add CONFIRM: yes only if removal is intentional.'],
    },
    'package': {
        'message': 'PIP needs a package name on the op line.',
        'why': 'The package name is used for PyPI metadata lookup.',
        'example': ['PIP chardet', 'ACTION: install'],
        'next': ['Put the PyPI package name after PIP.'],
    },
}


def _parse_request(parsed_op):
    """
    Return (action, package, import_name).

    Supported forms:

        PIP install chardet

        PIP uninstall chardet
        CONFIRM: yes

        PIP chardet
        ACTION: install

    Directive ACTION still works for compatibility.
    """
    directives = parsed_op.get('directives') or {}
    raw_target = (parsed_op.get('target') or '').strip()
    parts = raw_target.split()

    action = str(directives.get('ACTION') or '').strip().lower()
    package = raw_target

    if parts and parts[0].lower() in ('install', 'uninstall'):
        inline_action = parts[0].lower()
        inline_package = ' '.join(parts[1:]).strip()
        if not action:
            action = inline_action
        package = inline_package

    import_name = str(directives.get('IMPORT') or package).strip()
    return action, package, import_name

def validate(parsed_op):
    errors = []
    directives = parsed_op.get('directives') or {}
    action, package, import_name = _parse_request(parsed_op)

    if not package:
        errors.append('PIP requires a package name as target')

    if action not in ('install', 'uninstall'):
        errors.append('ACTION must be install or uninstall, or use inline syntax: PIP install package')

    if action == 'uninstall':
        confirm = str(directives.get('CONFIRM') or '').strip().lower()
        if confirm not in ('yes', 'true', '1', 'confirm'):
            errors.append('ACTION: uninstall requires CONFIRM: yes')

    return errors


def _project_root(ctx):
    return (ctx or {}).get('project_root') or os.path.expanduser('~/Documents')


def _site_packages(ctx):
    sp = os.path.join(_project_root(ctx), 'site-packages')
    if not os.path.isdir(sp):
        os.makedirs(sp)
    if sp not in sys.path:
        sys.path.insert(0, sp)
    return sp


def _tmp_wheel(ctx):
    return os.path.join(_project_root(ctx), '_forge_pip_tmp.whl')


def execute(ctx, parsed_op, result):
    action, package, import_name = _parse_request(parsed_op)

    sp = _site_packages(ctx)
    pypi_db = os.path.join(sp, '.pypi_packages')

    result['data'] = {
        'package': package,
        'import_name': import_name,
        'action': action,
        'site_packages': sp,
    }

    if action == 'install':
        _install(ctx, result, package, import_name, sp, pypi_db)
    else:
        _uninstall(result, package, import_name, sp, pypi_db)


def _install(ctx, result, package, import_name, sp, pypi_db):
    importlib.invalidate_caches()

    try:
        importlib.import_module(import_name)
        result['status'] = 'SKIPPED_ALREADY_PRESENT'
        result['message'] = "'%s' is already importable" % import_name
        result.setdefault('data', {})['already_present'] = True
        return
    except ImportError:
        pass

    try:
        with request.urlopen('https://pypi.org/pypi/%s/json' % package, timeout=15) as r:
            meta = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'PyPI fetch failed: %s' % e
        return

    info = meta.get('info') or {}
    version = info.get('version') or ''
    summary = info.get('summary') or ''

    wheel = None
    for item in meta.get('urls') or []:
        filename = item.get('filename') or ''
        if filename.endswith('.whl') and 'none-any' in filename:
            wheel = item
            break

    if not wheel:
        result['status'] = 'FAILED_IO'
        result['message'] = "No pure-Python wheel for '%s' %s. Package may require compiled extensions." % (
            package,
            version,
        )
        result.setdefault('data', {})['version'] = version
        return

    tmp = _tmp_wheel(ctx)

    try:
        with request.urlopen(wheel.get('url'), timeout=30) as r:
            data = r.read()
        with open(tmp, 'wb') as f:
            f.write(data)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Download failed: %s' % e
        return

    installed = []
    try:
        with zipfile.ZipFile(tmp) as zf:
            for name in zf.namelist():
                if not name or name.endswith('/'):
                    continue
                if '.dist-info/' in name:
                    continue

                dest = os.path.join(sp, name)
                parent = os.path.dirname(dest)
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent)

                with zf.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
                installed.append(dest)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Extraction failed: %s' % e
        return
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    importlib.invalidate_caches()
    try:
        importlib.import_module(import_name)
    except ImportError as e:
        result['status'] = 'FAILED_INSTALL'
        result['message'] = 'Extracted but import failed: %s' % e
        result.setdefault('data', {})['installed_count'] = len(installed)
        return

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
    result['message'] = "Installed '%s' %s (%d files)" % (package, version, len(installed))
    result.setdefault('data', {}).update({
        'version': version,
        'summary': summary,
        'installed_count': len(installed),
        'wheel': wheel.get('filename') or '',
    })


def _uninstall(result, package, import_name, sp, pypi_db):
    cfg = configparser.ConfigParser()
    if os.path.exists(pypi_db):
        cfg.read(pypi_db, encoding='utf-8')

    section = None
    for s in cfg.sections():
        if s.lower() == package.lower():
            section = s
            break

    removed = []
    cleanup_dirs = set()

    def note_removed(path):
        removed.append(path)
        parent = os.path.dirname(path)
        while parent and os.path.abspath(parent).startswith(os.path.abspath(sp)):
            cleanup_dirs.add(parent)
            if os.path.abspath(parent) == os.path.abspath(sp):
                break
            parent = os.path.dirname(parent)

    if section:
        files_str = cfg[section].get('files', '')
        for raw in files_str.split(','):
            raw = raw.strip()
            if not raw:
                continue

            abs_path = raw
            marker = 'site-packages/'
            if marker in raw:
                rel = raw.split(marker, 1)[1]
                abs_path = os.path.join(sp, rel)

            if os.path.isfile(abs_path):
                os.remove(abs_path)
                note_removed(abs_path)
            elif os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
                note_removed(abs_path)

        cfg.remove_section(section)
        with open(pypi_db, 'w', encoding='utf-8') as f:
            cfg.write(f)

    else:
        pkg_dir = os.path.join(sp, import_name)
        pkg_file = os.path.join(sp, import_name + '.py')

        if os.path.isdir(pkg_dir):
            shutil.rmtree(pkg_dir)
            note_removed(pkg_dir)
        elif os.path.isfile(pkg_file):
            os.remove(pkg_file)
            note_removed(pkg_file)
        else:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = "'%s' not found in .pypi_packages or site-packages" % package
            return

    # Clean empty directories left behind by file-by-file registry removal.
    for path in sorted(cleanup_dirs, key=lambda p: len(p), reverse=True):
        if os.path.abspath(path) == os.path.abspath(sp):
            continue
        try:
            if os.path.isdir(path) and not os.listdir(path):
                os.rmdir(path)
        except Exception:
            pass

    # If the import package directory still exists but only contains empty
    # residue, remove it. This prevents namespace-style imports after uninstall.
    pkg_dir = os.path.join(sp, import_name)
    if os.path.isdir(pkg_dir):
        try:
            if not any(True for _root, _dirs, files in os.walk(pkg_dir) for _f in files):
                shutil.rmtree(pkg_dir)
                if pkg_dir not in removed:
                    removed.append(pkg_dir)
        except Exception:
            pass

    # Evict package and submodules from module cache.
    prefix = import_name + '.'
    for key in list(sys.modules.keys()):
        if key == import_name or key.startswith(prefix):
            sys.modules.pop(key, None)

    importlib.invalidate_caches()

    result['status'] = 'APPLIED'
    result['message'] = "Uninstalled '%s' (%d item(s) removed)" % (package, len(removed))
    result.setdefault('data', {})['removed_count'] = len(removed)
