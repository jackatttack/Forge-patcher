# -*- coding: utf-8 -*-
"""
Forge entry point for Python IDE on iOS.

Clipboard loop:
- read a Forge bundle from the iOS clipboard
- run it against the Python IDE Workspace
- copy the returned Forge packet back to the clipboard
- print the same output in the terminal

This adapter deliberately avoids Pythonista's ~/Documents assumption.
"""

from __future__ import print_function

import importlib.util
import os
import sys
import traceback


FORGE_HOME = os.path.abspath(os.path.dirname(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.dirname(FORGE_HOME))
ENTRY_PATH = os.path.join(FORGE_HOME, 'entry.py')


def _configure():
    os.environ['FORGE_HOME'] = FORGE_HOME
    os.environ['FORGE_PROJECT_ROOT'] = WORKSPACE_ROOT

    if FORGE_HOME not in sys.path:
        sys.path.insert(0, FORGE_HOME)


def _load_entry():
    _configure()

    if not os.path.isfile(ENTRY_PATH):
        raise RuntimeError('Forge entry.py is missing: ' + ENTRY_PATH)

    spec = importlib.util.spec_from_file_location(
        'forge_pythonide_runtime_entry',
        ENTRY_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('Could not load Forge entry.py')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_clipboard():
    try:
        import clipboard
    except Exception as e:
        raise RuntimeError(
            'Python IDE clipboard module is unavailable: %s: %s'
            % (type(e).__name__, e)
        )

    try:
        value = clipboard.get()
    except Exception as e:
        raise RuntimeError(
            'Could not read clipboard: %s: %s'
            % (type(e).__name__, e)
        )

    if value is None:
        return ''
    return str(value)


def _write_clipboard(text):
    try:
        import clipboard
        clipboard.set(str(text))
        return True, ''
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)


def _raw_clipboard_result(run):
    """Return source text for an applied Forge CLIPBOARD op."""
    run = run or {}
    chosen = None

    for result in run.get('results') or []:
        if not isinstance(result, dict):
            continue

        op_name = str(result.get('op') or '').strip().upper()
        status = str(result.get('status') or '').strip().upper()

        if op_name == 'CLIPBOARD' and status == 'APPLIED':
            chosen = result

    if not chosen:
        return None

    data = chosen.get('data') or {}
    target = (
        chosen.get('file')
        or data.get('path')
        or chosen.get('target')
        or ''
    )
    target = str(target or '').strip().replace('\\', '/').lstrip('/')

    if not target:
        return None

    root = os.path.abspath(WORKSPACE_ROOT)
    abs_path = os.path.abspath(os.path.join(root, target))

    if not (
        abs_path == root
        or abs_path.startswith(root + os.sep)
    ):
        return None

    if not os.path.isfile(abs_path):
        return None

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return None


def _format_output(run):
    run = run or {}

    raw = _raw_clipboard_result(run)
    if raw is not None:
        return raw

    packet = run.get('packet') or ''
    stamp = run.get('stamp') or '?'

    parts = ['=== FORGE CLIPBOARD RETURN ===']
    if packet:
        parts.append(str(packet).rstrip())

    output = '\n'.join(parts).rstrip() + '\n'

    limit = 100000
    if len(output) <= limit:
        return output

    footer = [
        '',
        '=== OUTPUT TRUNCATED ===',
        'Clipboard return limited to %d chars.' % limit,
        'Full run was still stored on disk.',
        '',
        'To inspect the full packet, run:',
        'RUNS show %s' % stamp,
        '',
        'Run artifacts:',
        os.path.join(
            os.path.relpath(FORGE_HOME, WORKSPACE_ROOT),
            'artifacts',
            'runs',
            str(stamp),
        ),
    ]

    footer_text = '\n'.join(footer).rstrip() + '\n'
    room = max(0, limit - len(footer_text) - 1)

    return (
        output[:room].rstrip()
        + '\n'
        + footer_text
    )


def _bundle_from_argv():
    """Read an optional bundle file; otherwise use the clipboard."""
    if len(sys.argv) <= 1:
        return _read_clipboard()

    path = str(sys.argv[1] or '').strip()
    if not path:
        return _read_clipboard()

    if not os.path.isabs(path):
        path = os.path.join(WORKSPACE_ROOT, path)

    path = os.path.abspath(path)

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _error_output(exc):
    return (
        '=== FORGE CLIPBOARD RETURN ===\n'
        '=== FORGE PYTHON IDE ERROR ===\n'
        '%s: %s\n\n%s'
        % (
            type(exc).__name__,
            exc,
            traceback.format_exc(),
        )
    )


def main():
    try:
        bundle = _bundle_from_argv()

        if not str(bundle or '').strip():
            raise RuntimeError(
                'Clipboard is empty. Copy a Forge bundle, then run forge_entry.py again.'
            )

        entry = _load_entry()
        run = entry.run_from_text(
            bundle,
            project_root=WORKSPACE_ROOT,
            mode='dev',
            store=True,
        )

        output = _format_output(run)

    except Exception as e:
        output = _error_output(e)

    ok, clipboard_error = _write_clipboard(output)

    print(output, end='' if output.endswith('\n') else '\n')

    if ok:
        print('')
        print('Forge return copied to clipboard.')
    else:
        print('')
        print('WARNING: could not copy Forge return to clipboard:')
        print(clipboard_error)

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
