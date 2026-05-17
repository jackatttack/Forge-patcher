# -*- coding: utf-8 -*-
"""
REVERT_RUN reboot op.
"""


SPEC = {
    'name': 'REVERT_RUN',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS', 'CONFIRM']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Restore touched files to their pre-run state using stored snapshots.',
    'minimal_example': [
        'REVERT_RUN 20260511_120000',
    ],
}


HINTS = {
    '_max_hints': 1,
    'run': {
        'message': 'REVERT_RUN needs a stored run id.',
        'why': 'Revert uses the recovery snapshots saved with a previous mutating run.',
        'example': [
            'RUNS latest',
            '',
            'REVERT_RUN 20260511_120000',
        ],
        'next': [
            'Run RUNS latest.',
            'Copy the stamp exactly.',
            'Use DIFF first if you want to inspect the stored change.',
        ],
    },
}

def validate(parsed_op):
    args = ((parsed_op.get('directives') or {}).get('ARGS') or parsed_op.get('target') or '').strip()
    if not args:
        return ['REVERT_RUN requires a run stamp']
    return []


def execute(ctx, parsed_op, result):
    from forge_core.run_storage import revert_run

    args = ((parsed_op.get('directives') or {}).get('ARGS') or parsed_op.get('target') or '').strip()
    ok, msg = revert_run(ctx.get('project_root'), args)

    result['status'] = 'APPLIED' if ok else 'FAILED_IO'
    result['message'] = msg
