# -*- coding: utf-8 -*-
"""
ops.shortcut
============
Fire an iOS Shortcut by name.

Usage:
    SHORTCUT My Shortcut Name

Fires the Shortcut via the shortcuts:// URL scheme.
Fire and forget - no return value captured.
"""

import webbrowser
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'SHORTCUT',
    'target_kind': 'file',
    'body_mode': 'none',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Fire a named iOS Shortcut by name.',
}


def validate(parsed_op):
    """Check shortcut name is present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('SHORTCUT requires a shortcut name as target')
    return errors


def execute(ctx, parsed_op, result):
    """Fire a named iOS Shortcut via URL scheme."""
    name = (parsed_op.target or '').strip()
    url = 'shortcuts://run-shortcut?name=' + quote(name)
    try:
        webbrowser.open(url)
        result['status'] = 'APPLIED'
        result['message'] = 'Fired: ' + name
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = type(e).__name__ + ': ' + str(e)
