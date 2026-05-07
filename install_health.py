# -*- coding: utf-8 -*-
"""
install_health.py
=================

Read-only Forge install health check.

Run this when Forge opens strangely, LinkOS buttons do not work, imports fail,
or you are unsure whether you are in contained mode or root-router mode.

This script is deliberately safe:
- no Forge imports
- no file changes
- no network access
- no installer actions

It prints a simple verdict first, then details.
"""

from __future__ import print_function

import os


MARKER = 'FORGE_ROOT_ROUTER'


def documents_root():
    return os.path.abspath(os.path.expanduser('~/Documents'))


def here():
    return os.path.abspath(os.path.dirname(__file__))


def exists(path):
    return os.path.exists(path)


def rel_exists(rel):
    return exists(os.path.join(here(), rel))


def contains(path, needle):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return needle in f.read(5000)
    except Exception:
        return False


def yesno(value):
    return 'yes' if value else 'no'


def check():
    docs = documents_root()
    root_entry = os.path.join(docs, 'forge_entry.py')
    root_linkos = os.path.join(docs, 'linkos.py')
    root_shadow = os.path.join(docs, 'forge')

    data = {
        'install_root': here(),
        'documents_root': docs,
        'contained_entry': rel_exists('forge_entry.py'),
        'contained_linkos': rel_exists('linkos.py'),
        'forge_package': rel_exists('forge'),
        'forge_entry_module': rel_exists('forge/entry.py'),
        'linkos_router': rel_exists('forge/extensions/linkos/router.py'),
        'llm_guide': rel_exists('docs/AI_FIRST_BOOT.txt'),
        'boot_bundle': rel_exists('docs/MINIMAL_BOOT_BUNDLE.txt'),
        'root_entry': exists(root_entry),
        'root_linkos': exists(root_linkos),
        'root_entry_marker': contains(root_entry, MARKER),
        'root_linkos_marker': contains(root_linkos, MARKER),
        'root_shadow_forge': os.path.isdir(root_shadow),
        'smoke': rel_exists('forge_public_smoke.py'),
    }
    data['root_router'] = data['root_entry_marker'] or data['root_linkos_marker']
    return data


def verdict(data):
    issues = []

    if not data['contained_entry']:
        issues.append('forge_entry.py is missing from this install folder.')
    if not data['forge_package']:
        issues.append('forge/ package is missing from this install folder.')
    if not data['forge_entry_module']:
        issues.append('forge/entry.py is missing.')
    if not data['linkos_router']:
        issues.append('LinkOS router is missing.')
    if not data['llm_guide']:
        issues.append('docs/AI_FIRST_BOOT.txt is missing.')
    if data['root_shadow_forge']:
        issues.append('A lowercase ~/Documents/forge folder exists and may shadow this install.')

    if issues:
        return 'Possible issue', issues

    if data['root_router']:
        return 'Looks healthy — root router mode', []

    return 'Looks healthy — contained mode', []


def line():
    print('═' * 48)


def main():
    data = check()
    status, issues = verdict(data)

    line()
    print('              FORGE INSTALL HEALTH')
    line()
    print('')
    print('Status: ' + status)

    if data['root_router']:
        print('Mode: root router / tappable links likely active')
    else:
        print('Mode: contained / display-only links may be normal')

    print('')

    if issues:
        print('Issues:')
        for item in issues:
            print('- ' + item)
        print('')
        print('Safe next steps:')
        print('1. Fully close and reopen Pythonista.')
        print('2. Run start_here.py for orientation.')
        print('3. If root launchers are needed, run install_root_router.py from the Forge folder.')
    else:
        print('Next safe test:')
        print('1. Put HELP HELP on the clipboard.')
        print('2. Run forge_entry.py.')
        print('3. Confirm a HELP packet appears.')

    print('')
    print('Details:')
    keys = [
        'install_root',
        'documents_root',
        'contained_entry',
        'contained_linkos',
        'forge_package',
        'forge_entry_module',
        'linkos_router',
        'llm_guide',
        'boot_bundle',
        'root_entry',
        'root_linkos',
        'root_entry_marker',
        'root_linkos_marker',
        'root_shadow_forge',
        'smoke',
    ]
    for key in keys:
        value = data[key]
        if isinstance(value, bool):
            value = yesno(value)
        print('- %s: %s' % (key, value))

    print('')
    line()


if __name__ == '__main__':
    main()
