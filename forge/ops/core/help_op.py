# -*- coding: utf-8 -*-
"""
ops.help_op
===========

Human-facing HELP for public Forge.

HELP has two jobs:

1. Bare HELP is the user lifeboat. It renders Start Here guidance.
2. HELP <OP> remains the exact technical syntax reference for registered ops.

It also supports human topics such as install, root, run-missing,
module-not-found, buttons, install-health, and where-am-i.
"""

SPEC = {
    'name': 'HELP',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Show human help, topic guidance, or exact syntax for one registered op.',
    'subject': [
        'No subject renders the Start Here help page.',
        'Registered op name, for example READ_FILE, renders exact syntax.',
        'Human topics such as install, root, run-missing, buttons, or module-not-found render guidance.',
    ],
    'common_failures': [
        'Unknown op or help topic.',
        'File path target does not exist under project root.',
    ],
    'safe_usage': [
        'Run HELP by itself when you are new or stuck.',
        'Run HELP HELP for exact syntax for the HELP op.',
        'Run HELP <OP_NAME> for exact op syntax.',
        'Run start_here.py or install_health.py manually if Forge feels unhealthy.',
    ],
    'minimal_example': [
        'HELP',
        '',
        'HELP HELP',
        '',
        'HELP RUN_FILE',
        '',
        'HELP install',
        '',
        'HELP module-not-found',
    ],
    'related_ops': ['LIST_OPS', 'DOCS'],
}

HINTS = {
    '_max_hints': 1,
    'unknown op': {
        'message': 'Unknown op or help topic.',
        'why': 'The requested op or topic is not currently registered in this Forge entry point.',
        'priority': 120,
        'example': [
            'HELP',
            '',
            'HELP HELP',
            '',
            'HELP install',
            '',
            'LIST_OPS',
        ],
        'next': ['Run HELP for Start Here guidance', 'Run LIST_OPS to discover registered ops'],
    },
    'file not found': {
        'message': 'Help target file was not found.',
        'why': 'HELP can show module docstrings for files, but the path must exist under project root.',
        'priority': 120,
        'example': [
            'LIST_FILES forge/ops/core',
            '',
            'HELP forge/ops/core/help_op.py',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
}


def validate(parsed_op):
    """HELP is intentionally always allowed.

    No subject is the public human lifeboat. HELP <OP> remains the exact
    technical reference path.
    """
    return []


def _start_here_text():
    """Dependency-light human help fallback for bare HELP."""
    return '''=== FORGE HELP / START HERE ===

Forge is a local Pythonista harness for working with an LLM.

The loop:
1. The LLM gives you a plain-text Forge bundle.
2. You copy it.
3. You run forge_entry.py.
4. Forge runs the bundle locally.
5. Forge returns a run packet.
6. You paste the packet back.

The run packet is the source of truth.

First safe path:
- Run forge_entry.py once.
- Open AI_FIRST_BOOT.txt at the root of this project.
- Paste that text into an LLM.
- Copy the small bundle the LLM gives you.
- Run forge_entry.py again.

If something looks wrong:
- Buttons do not tap: contained mode may be active. Run forge_entry.py manually.
- RUN MISSING: the visual run page could not find saved details; the packet above may still be valid.
- Failed parse: your clipboard probably did not contain a valid Forge bundle.
- ModuleNotFoundError: restart Pythonista, then run install_health.py.
- Cannot see your files: root launcher mode is optional.

Useful files:
- AI_FIRST_BOOT.txt - paste this into an LLM
- start_here.py - standalone orientation lifeboat
- install_health.py - read-only install checker
- forge_entry.py - run the Forge clipboard loop
- install_root_router.py - optional root/tappable-link mode
- forge_public_smoke.py - sanity check

For exact command syntax:
- HELP HELP
- HELP RUN_FILE
- LIST_OPS

'''


def _root_help_text():
    """Return dependency-light root mode help."""
    return '''=== ROOT LAUNCHER MODE HELP ===

Contained mode works without root access.

Root launcher mode is optional. It installs small launchers at Pythonista
Documents root:
- forge_entry.py
- linkos.py

Benefits:
- tappable LinkOS links
- easier Shortcut setup
- wider workspace access

Risk:
- Forge can inspect and patch more files.

Only enable it deliberately with install_root_router.py.

'''


def _topic_help(name):
    """Return human topic help for common public-user states."""
    key = (name or '').strip().lower().replace('_', '-')

    topics = {
        'start-here': _start_here_text(),
        'start': _start_here_text(),
        'where-am-i': '''=== WHERE AM I HELP ===

Use this when Forge opens but you are unsure what folder, mode, or install
state you are in.

Safe checks:
1. Run install_health.py.
2. Run start_here.py.
3. Run HELP HELP.
4. Run LIST_FILES . in a Forge bundle to see the active Forge root.

''',
        'install': '''=== FORGE INSTALL HELP ===

For easiest setup:
- create install_forge.py in Pythonista
- paste the public installer script
- run it

This installs Forge into:
- ~/Documents/Forge

After install:
- open Forge/forge_entry.py
- run it once
- open AI_FIRST_BOOT.txt and paste it into an LLM

Contained mode is the safe default.

Useful files:
- AI_FIRST_BOOT.txt - LLM handoff guide
- start_here.py - orientation
- install_health.py - read-only health check
- install_root_router.py - optional root/tappable-link mode
- forge_public_smoke.py - sanity check

''',
        'install-health': '''=== FORGE INSTALL HEALTH HELP ===

Run install_health.py when:
- LinkOS buttons do not work
- imports fail
- Forge opens strangely
- you are unsure whether root router mode is active

install_health.py is read-only.
It does not move, delete, install, or repair files.

''',
        'run-missing': '''=== RUN MISSING HELP ===

RUN MISSING means LinkOS tried to open the visual page for a run, but could
not find the saved run manifest.

This does not always mean the bundle failed.
The packet above may still be valid.

Try:
1. Run HELP HELP to test Forge.
2. Run start_here.py if unsure.
3. Run install_health.py if imports or launchers seem wrong.

''',
        'module-not-found': '''=== MODULE NOT FOUND HELP ===

ModuleNotFoundError usually means Python imported the wrong package, a file is
missing, or Pythonista has stale imports cached.

Safe steps:
1. Fully close Pythonista from the app switcher.
2. Reopen it.
3. Run install_health.py.
4. Check for a lowercase ~/Documents/forge folder shadowing ~/Documents/Forge/forge.
5. Do not guess paths. Inspect from the packet or install_health.py output.

''',
        'buttons': '''=== LINKOS BUTTON HELP ===

If LinkOS renders but buttons do not tap, you are probably in contained mode.

That is not a broken install.
Run forge_entry.py manually.

For tappable buttons, install optional root launcher mode with:
- install_root_router.py

''',
        'root': _root_help_text(),
        'root-mode': _root_help_text(),
        'root-launcher-mode': _root_help_text(),
    }

    return topics.get(key)


def execute(ctx, parsed_op, result):
    """Render Start Here, topic guidance, file help, or registered op HELP."""
    from forge.op_help import render_op_help

    name = (parsed_op.target or '').strip() or (parsed_op.directives.get('ARGS') or '').strip()

    if not name:
        result['status'] = 'APPLIED'
        result['message'] = 'Start Here help'
        result['preview'] = _start_here_text()
        return

    topic = _topic_help(name)
    if topic is not None:
        result['status'] = 'APPLIED'
        result['message'] = 'Help for ' + name
        result['preview'] = topic
        return

    if '/' in name or name.endswith('.py'):
        from forge.op_help import _render_file_help

        rel = name
        text = _render_file_help(rel)
        if text is None:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = 'File not found: ' + rel
            return

        result['status'] = 'APPLIED'
        result['message'] = 'Help for ' + rel
        result['preview'] = text
        return

    text = render_op_help(name)
    if text is None:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Unknown op or help topic: ' + name
        return

    result['status'] = 'APPLIED'
    result['message'] = 'Help for ' + name.upper()
    result['preview'] = text
