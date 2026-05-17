# -*- coding: utf-8 -*-
"""
Public smoke test for Forge.

This is intentionally small and portable.

It verifies that the installed forge/ folder can:
- run a read-only bundle
- produce a packet
- store artifacts beside the active Forge home
- expose HELP
- inspect the local Forge folder without assuming a dev path

Run directly in Pythonista from inside the public install.
"""

from __future__ import print_function

import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))

if HERE not in sys.path:
    sys.path.insert(0, HERE)

os.environ['FORGE_HOME'] = HERE


from entry import run_from_text


def assert_true(name, condition):
    if not condition:
        raise AssertionError(name)
    print('PASS: ' + name)


def main():
    bundle = '\n'.join([
        'LIST_FILES .',
        'DEPTH: 2',
        'FILES: no',
        '',
        'HELP READ quick',
        '',
    ])

    run = run_from_text(bundle, project_root=HERE, mode='dev', store=True)

    packet = run.get('packet') or ''
    results = run.get('results') or []
    artifact_dir = run.get('artifact_dir') or ''

    assert_true('run applied', run.get('status') == 'APPLIED')
    assert_true('has stamp', bool(run.get('stamp')))
    packet_upper = packet.upper()
    assert_true('has packet', 'FORGE' in packet_upper and 'RUN' in packet_upper)
    assert_true('has two results', len(results) == 2)
    assert_true('list files applied', results[0].get('status') == 'APPLIED')
    assert_true('help applied', results[1].get('status') == 'APPLIED')
    assert_true('packet mentions LIST_FILES', 'LIST_FILES' in packet)
    assert_true('packet mentions HELP', 'HELP' in packet)
    assert_true('artifact dir exists', bool(artifact_dir) and os.path.isdir(artifact_dir))
    assert_true('artifact dir under forge home', os.path.realpath(artifact_dir).startswith(os.path.realpath(HERE) + os.sep))

    print('')
    print('FORGE PUBLIC SMOKE PASSED')
    print('forge_home: ' + HERE)
    print('artifact_dir: ' + artifact_dir)


if __name__ == '__main__':
    main()