# -*- coding: utf-8 -*-
"""
forge.cli_runner
=================
Shared execution engine for CLI wrapper ops (JOURNAL, SHEETS, NOTIFY, WS).

Provides:
  run_cli(cli_abs, argv, timeout)
      Execute a CLI script in-process. Returns capture dict.

  apply_result(result, op_name, capture, timeout)
      Populate result dict (status, message, preview) from capture.
"""

import io
import sys
import traceback
import threading


def run_cli(cli_abs, argv, timeout=20):
    """
    Execute a CLI script in-process and capture output.
    Returns dict: {exit_code, stdout, stderr, timed_out}
    """
    capture = {'exit_code': None, 'stdout': '', 'stderr': '', 'timed_out': False}
    t = threading.Thread(target=_run_code, args=(cli_abs, argv, capture))
    t.daemon = True
    t.start()
    t.join(timeout)
    if t.is_alive():
        capture['timed_out'] = True
    return capture


def apply_result(result, op_name, capture, timeout=20):
    """
    Populate result dict from a run_cli capture dict.
    """
    if capture['timed_out']:
        result['status']  = 'FAILED_PARSE'
        result['message'] = 'timeout after %ss' % timeout
        return

    exit_code = capture['exit_code']
    stdout    = capture['stdout'] or ''
    stderr    = capture['stderr'] or ''

    lines = ['%s [exit %s]' % (op_name, exit_code)]
    if stdout:
        lines += ['--- stdout ---', stdout.rstrip('\n')]
    if stderr:
        lines += ['--- stderr ---', stderr.rstrip('\n')]

    result['preview'] = '\n'.join(lines).rstrip() + '\n'

    if exit_code == 0:
        result['status']  = 'APPLIED'
        result['message'] = 'exit 0'
    else:
        result['status']  = 'FAILED_PARSE'
        result['message'] = 'exit %s' % exit_code


def _run_code(file_abs, argv, capture):
    """Execute Python code string in a subprocess and return stdout/stderr/exit."""
    old_argv   = sys.argv[:]
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    out_buf = io.StringIO()
    err_buf = io.StringIO()

    try:
        sys.argv   = argv[:]
        sys.stdout = out_buf
        sys.stderr = err_buf

        with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()

        compiled = compile(code, file_abs, 'exec')
        ns = {'__name__': '__main__', '__file__': file_abs, '__package__': None}
        exec(compiled, ns, ns)
        capture['exit_code'] = 0
    except SystemExit as e:
        code = e.code
        capture['exit_code'] = code if isinstance(code, int) else 1
        if code not in (None, '', 0):
            print(code, file=err_buf)
    except Exception:
        capture['exit_code'] = 1
        traceback.print_exc(file=err_buf)
    finally:
        capture['stdout'] = out_buf.getvalue()
        capture['stderr'] = err_buf.getvalue()
        sys.argv   = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
