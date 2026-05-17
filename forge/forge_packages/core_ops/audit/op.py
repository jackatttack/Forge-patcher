# -*- coding: utf-8 -*-
"""
AUDIT reboot op.

Checks the reboot's package-shaped op contract.

This establishes the principle:
Forge should be able to test and explain its own extension surface.
"""

import importlib.util
import os

from forge_core.registry import OPS_BY_NAME, discover_ops


SPEC = {
    'name': 'AUDIT',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(),
    'required_directives': set(),
}

HELP = {
    'summary': 'Audit reboot op package contract health.',
    'minimal_example': [
        'AUDIT',
    ],
}


HINTS = {
    '_max_hints': 1,
    'failure': {
        'message': 'AUDIT found a package contract problem.',
        'why': 'Reboot ops must keep a predictable package shape so discovery, HELP, tests, and agent guidance stay reliable.',
        'example': [
            'REBOOT_AUDIT',
            '',
            'LIST_FILES forge/forge_packages/core_ops',
        ],
        'next': [
            'Read the failing AUDIT line.',
            'Inspect the failing op folder.',
            'Fix manifest/op/README shape, then rerun tests and audit.',
        ],
    },
}

def validate(parsed_op):
    return []


def _ops_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _load_manifest(folder):
    path = os.path.join(folder, 'manifest.py')
    if not os.path.isfile(path):
        return None, 'missing manifest.py'

    try:
        mod_name = 'forge_reboot_manifest_' + os.path.basename(folder)
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        manifest = getattr(mod, 'MANIFEST', None)
        if not isinstance(manifest, dict):
            return None, 'MANIFEST is not a dict'
        return manifest, None
    except Exception as e:
        return None, 'manifest import failed: %s: %s' % (type(e).__name__, e)


def _check_op(name, mod):
    issues = []

    try:
        folder = os.path.dirname(os.path.abspath(getattr(mod, '__file__', '')))
    except Exception:
        folder = ''

    folder_name = os.path.basename(folder)

    if not os.path.isfile(os.path.join(folder, 'README.txt')):
        issues.append('missing README.txt')

    manifest, manifest_error = _load_manifest(folder)
    if manifest_error:
        issues.append(manifest_error)
    else:
        for key in ('name', 'op', 'kind', 'version', 'summary'):
            if key not in manifest:
                issues.append('MANIFEST missing ' + key)
        if manifest.get('name') != folder_name:
            issues.append('MANIFEST name mismatch')
        if str(manifest.get('op') or '').upper() != name:
            issues.append('MANIFEST op mismatch')
        if manifest.get('kind') != 'core-op':
            issues.append('MANIFEST kind should be core-op')

    spec = getattr(mod, 'SPEC', None)
    if not isinstance(spec, dict):
        issues.append('missing SPEC dict')
    else:
        for key in ('name', 'target_kind', 'body_mode', 'allowed_directives', 'required_directives'):
            if key not in spec:
                issues.append('SPEC missing ' + key)
        if str(spec.get('name') or '').upper() != name:
            issues.append('SPEC name mismatch')

    help_data = getattr(mod, 'HELP', None)
    if not isinstance(help_data, dict):
        issues.append('missing HELP dict')
    elif not help_data.get('summary'):
        issues.append('HELP missing summary')

    if not callable(getattr(mod, 'validate', None)):
        issues.append('missing validate()')

    if not callable(getattr(mod, 'execute', None)):
        issues.append('missing execute()')

    return issues


def execute(ctx, parsed_op, result):
    discover_ops()

    lines = []
    lines.append('REBOOT AUDIT')
    lines.append('')

    total = 0
    failed = 0

    for name in sorted(OPS_BY_NAME.keys()):
        total += 1
        mod = OPS_BY_NAME.get(name)
        issues = _check_op(name, mod)
        if issues:
            failed += 1
            lines.append('- FAIL %-12s %s' % (name, '; '.join(issues)))
        else:
            lines.append('- PASS %-12s package contract ok' % name)

    lines.append('')
    lines.append('total: %d' % total)
    lines.append('failed: %d' % failed)

    if failed:
        result['status'] = 'FAILED_VALIDATE'
        result['message'] = '%d audit failure(s)' % failed
    else:
        result['status'] = 'APPLIED'
        result['message'] = 'audit clean'

    result['preview'] = '\n'.join(lines)
    result['data'] = {
        'total': total,
        'failed': failed,
    }
