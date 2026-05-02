# -*- coding: utf-8 -*-
"""
ops.revert_run
==============
Revert a previous forge run by stamp.

Usage:
    REVERT_RUN 20260324_165056
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REVERT_RUN',
    'target_kind': 'file',
    'body_mode': 'none',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Restore files to their pre-run state using snapshots from a previous run.',
}


def validate(parsed_op):
    """Check run ID is present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REVERT_RUN requires a run stamp as target')
    return errors


def execute(ctx, parsed_op, result):
    """Restore files to their pre-run state using snapshots from a previous run."""
    from forge.run_storage import revert_run
    stamp = (parsed_op.target or '').strip()
    ok, msg = revert_run(ctx.project_root, stamp)
    result['status'] = 'APPLIED' if ok else 'FAILED_IO'
    result['message'] = msg
