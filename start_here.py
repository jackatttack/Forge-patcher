# -*- coding: utf-8 -*-
"""
start_here.py
=============

Forge lifeboat page.

Run this file when you are new, stuck, unsure what Forge is doing, or when
LinkOS/HELP output feels confusing.

This script is deliberately boring and safe:
- no Forge imports
- no LinkOS dependency
- no file changes
- no installer actions
- no network access

It only prints a human-readable orientation page.
"""

from __future__ import print_function

import os


def documents_root():
    return os.path.abspath(os.path.expanduser('~/Documents'))


def here():
    return os.path.abspath(os.path.dirname(__file__))


def exists(rel):
    return os.path.exists(os.path.join(here(), rel))


def root_exists(name):
    return os.path.exists(os.path.join(documents_root(), name))


def file_contains(path, needle):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return needle in f.read(4000)
    except Exception:
        return False


def yesno(value):
    return 'yes' if value else 'no'


def line():
    print('═' * 48)


def section(title):
    print('')
    print(title.upper())
    print('─' * len(title))


def bullet(text):
    print('- ' + text)


def status():
    docs = documents_root()
    root_entry = os.path.join(docs, 'forge_entry.py')
    root_linkos = os.path.join(docs, 'linkos.py')
    root_router = (
        file_contains(root_entry, 'FORGE_ROOT_ROUTER') or
        file_contains(root_linkos, 'FORGE_ROOT_ROUTER')
    )

    print('Detected:')
    print('- this folder: ' + here())
    print('- forge_entry.py here: ' + yesno(exists('forge_entry.py')))
    print('- Forge package here: ' + yesno(exists('forge')))
    print('- LLM first-boot guide: ' + yesno(exists('docs/AI_FIRST_BOOT.txt')))
    print('- install health script: ' + yesno(exists('install_health.py')))
    print('- root launcher present: ' + yesno(root_exists('forge_entry.py')))
    print('- root router marker: ' + yesno(root_router))
    print('- root lowercase forge/ shadow risk: ' + yesno(os.path.isdir(os.path.join(docs, 'forge'))))


def main():
    line()
    print('              FORGE START HERE')
    print('          safe orientation page')
    line()

    print('')
    status()

    section('What Forge is')
    print('Forge is a local Pythonista harness for working with an LLM.')
    print('The LLM gives you a plain-text Forge bundle. You choose when to run it.')
    print('Forge runs it locally and returns a run packet.')
    print('')
    print('The run packet is the source of truth.')

    section('First safe path')
    print('1. Run forge_entry.py once.')
    print('2. Open docs/AI_FIRST_BOOT.txt.')
    print('3. Paste that text into an LLM.')
    print('4. The LLM will give you a small runnable Forge bundle.')
    print('5. Copy the bundle, run forge_entry.py, and paste the packet back.')

    section('If something looks wrong')
    bullet('Buttons do not tap: contained mode may be active. Run forge_entry.py manually.')
    bullet('RUN MISSING: the visual run page could not find saved run details; the packet above may still be valid.')
    bullet('Failed parse: your clipboard probably did not contain a valid Forge bundle.')
    bullet('ModuleNotFoundError: fully restart Pythonista, then run install_health.py.')
    bullet('Cannot see your files: Forge may be in contained mode. Root launcher mode is optional.')

    section('Useful files')
    bullet('forge_entry.py — runs the Forge clipboard loop')
    bullet('docs/AI_FIRST_BOOT.txt — paste this into an LLM')
    bullet('install_health.py — checks install state without changing files')
    bullet('install_root_router.py — optional root/tappable-link mode')
    bullet('forge_public_smoke.py — sanity check after install/update')

    section('Important rule')
    print('Forge should never require blind trust.')
    print('Inspect first. Keep changes small. Trust the packet.')

    print('')
    line()
    print('If in doubt: run HELP, start_here.py, or install_health.py.')
    line()


if __name__ == '__main__':
    main()
