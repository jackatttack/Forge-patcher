# -*- coding: utf-8 -*-
"""
ops.run_file
============
RUN_FILE op — execute a Python file and capture its output.

Runs a script under project root in an isolated namespace, capturing
stdout, stderr, and exit code. Supports ARGS for command-line parameters,
CLIP to copy stdout to clipboard, and TIMEOUT to cap execution time.
Use for probes, test scripts, and CLI wrappers.
"""

import io
import os
import sys
import traceback
import threading

from forge.file_ops import resolve_under_root, in_root

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'RUN_FILE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS', 'TIMEOUT', 'CLIP']),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP RUN_FILE.
HELP = {
    'summary': 'Execute a Python file under project root and capture stdout and stderr.',
    'subject': ['Relative Python file path inside project root.'],
    'common_failures': [
        'File not found.',
        'Target escapes project root.',
        'Script exits non-zero.',
        'Execution timeout after 20 seconds.',
        'Missing or invalid target.',
        'Absolute or escaping paths are rejected.',
    ],
    'safe_usage': [
        'Use this for probes and verification after patches.',
        'When testing imported modules after patching, remember module cache can affect results.',
        'Use ARGS when the script expects command-line parameters.',
        'Use relative paths only.',
    ],
    'minimal_example': [
        'RUN_FILE test_probe.py',
        'ARGS: alpha beta',
    ],
    'related_ops': ['READ_FILE', 'PREVIEW', 'DIFF'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'target': 'Provide a relative path to the .py file to run — e.g. RUN_FILE utils/myscript.py',
    'not found': 'File not found — check the path is relative to project root',
}


def validate(parsed_op):
    """Check that target file path is present. Returns list of error strings."""
    errors = []
    if not (parsed_op.target or '').strip():
        errors.append('RUN_FILE requires a target path')
    return errors


def _run_code(file_abs, argv, capture):
    """Execute code in an isolated namespace, capture stdout/stderr."""
    old_argv = sys.argv[:]
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    # RUN_FILE executes in-process, so scripts can accidentally poison shared
    # module state. Preserve common Pythonista/system modules that must remain
    # real after probes finish.
    _missing = object()
    protected_modules = ('clipboard',)
    old_modules = {}
    for name in protected_modules:
        old_modules[name] = sys.modules.get(name, _missing)

    ns = {
        '__name__': '__main__',
        '__file__': file_abs,
        '__package__': None,
    }

    out_buf = io.StringIO()
    err_buf = io.StringIO()

    try:
        sys.argv = argv[:]
        sys.stdout = out_buf
        sys.stderr = err_buf

        with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()

        compiled = compile(code, file_abs, 'exec')
        exec(compiled, ns, ns)
        capture['exit_code'] = 0
    except SystemExit as e:
        code = e.code
        if isinstance(code, int):
            capture['exit_code'] = code
        else:
            capture['exit_code'] = 1
            if code not in (None, ''):
                print(code, file=err_buf)
    except Exception:
        capture['exit_code'] = 1
        traceback.print_exc(file=err_buf)
    finally:
        capture['stdout'] = out_buf.getvalue()
        capture['stderr'] = err_buf.getvalue()
        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        for name, old_value in old_modules.items():
            try:
                if old_value is _missing:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = old_value
            except Exception:
                pass

def execute(ctx, parsed_op, result):
    """Resolve and execute a Python file, capturing stdout, stderr, and exit code."""
    file_abs = resolve_under_root(ctx.project_root, parsed_op.target)

    if not in_root(ctx.project_root, file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    raw_args = (parsed_op.directives.get('ARGS') or '').strip()
    extra_args = raw_args.split() if raw_args else []
    argv = [file_abs] + extra_args

    capture = {
        'exit_code': None,
        'stdout': '',
        'stderr': '',
    }

    timeout = int(parsed_op.directives.get('TIMEOUT') or _TIMEOUT_SECONDS)

    t = threading.Thread(target=_run_code, args=(file_abs, argv, capture))
    t.daemon = True
    t.start()
    t.join(timeout)

    if t.is_alive():
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'timeout after %ss' % timeout
        result['preview'] = 'RUN_FILE %s [timeout]' % parsed_op.target
        result['file'] = parsed_op.target
        return

    exit_code = capture.get('exit_code')
    stdout = capture.get('stdout') or ''
    stderr = capture.get('stderr') or ''

    clip = (parsed_op.directives.get('CLIP') or '').strip().lower() == 'yes'

    if clip and stdout:
        result['clip_result'] = stdout.strip()

    stdout_clean = stdout.strip()
    result['file'] = parsed_op.target
    result['stdout'] = stdout_clean
    result['preview'] = _format_preview(parsed_op.target, exit_code, stdout, stderr, clipped=clip)
    result['out'] = {
        'stdout': stdout_clean,
        'lines': [l for l in stdout_clean.splitlines() if l.strip()],
        'exit_code': exit_code,
        'stderr': stderr.strip(),
    }

    if exit_code == 0:
        result['status'] = 'APPLIED'
        result['message'] = 'exit 0'
    else:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'exit %s' % exit_code

def _format_preview(target, exit_code, stdout, stderr, clipped=False):
    """Format stdout/stderr output into a compact preview string for the run packet."""
    lines = ['RUN_FILE %s [exit %s]' % (target, exit_code)]
    if stdout:
        lines.append('--- stdout ---')
        lines.append(stdout.rstrip('\n'))
        if clipped:
            lines.append('[clipped]')
    if stderr:
        lines.append('--- stderr ---')
        lines.append(stderr.rstrip('\n'))
    return '\n'.join(lines).rstrip() + '\n'
# Subprocess execution timeout in seconds.


_TIMEOUT_SECONDS = 20
