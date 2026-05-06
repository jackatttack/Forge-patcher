# -*- coding: utf-8 -*-
"""
LINKOS op
=========

Render Forge LinkOS pages from a Forge bundle.
"""

SPEC = {
    'name': 'LINKOS',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
    'summary': 'Render Forge LinkOS, the text-first link command surface.',
}

HELP = {
    'summary': 'Render Forge LinkOS, the text-first link command surface for Pythonista.',
    'subject': [
        'No subject. Use ARGS to choose a LinkOS route.',
    ],
    'optional_directives': [
        'ARGS — LinkOS route, e.g. home, files forge, run latest.',
    ],
    'body': [
        'Forbidden.',
    ],
    'common_failures': [
        'Unknown LinkOS command.',
        'A file route points to a missing path.',
        'Pythonista console links do not always appear in captured stdout, so LinkOS prints visible labels too.',
    ],
    'safe_usage': [
        'Use LINKOS as a quick navigation/action surface.',
        'Use LINKOS home for the command centre.',
        'Use LINKOS files <path> to browse files.',
        'Use LINKOS run <stamp> for run-focused action panels.',
    ],
    'related_ops': ['HELP', 'DOCS', 'LIST_FILES', 'LIST_RUNS', 'DIFF'],
    'minimal_example': [
        'LINKOS',
        'ARGS: home',
        '',
        'LINKOS',
        'ARGS: files forge',
        '',
        'LINKOS',
        'ARGS: run latest',
    ],
}

HINTS = {
    '_max_hints': 1,
    'unknown': {
        'message': 'LINKOS route was not recognised.',
        'why': 'LinkOS routes through simple command words such as home, files, run, docs, safety, and help.',
        'priority': 100,
        'example': [
            'LINKOS',
            'ARGS: home',
        ],
        'next': ['Use ARGS: home', 'HELP LINKOS'],
    },
}


def validate(parsed_op):
    return []


def execute(ctx, parsed_op, result):
    """Render LinkOS into the run packet instead of printing live.

    Pythonista's console lands at the bottom after forge_entry prints the
    packet. Capturing the LinkOS render here means the rendered surface appears
    inside === PREVIEW === after earlier output. If LINKOS is the last op in a
    bundle, LinkOS becomes the final visible console surface.
    """
    args_raw = (parsed_op.directives.get('ARGS') or 'home').strip()
    argv = args_raw.split() if args_raw else ['home']

    import io
    import sys

    buf = io.StringIO()
    old_stdout = sys.stdout

    try:
        stale = [
            name for name in list(sys.modules.keys())
            if name == 'forge.extensions.linkos'
            or name.startswith('forge.extensions.linkos.')
        ]
        for name in stale:
            try:
                del sys.modules[name]
            except Exception:
                pass

        import forge.extensions.linkos.router as router

        sys.stdout = buf
        try:
            router.dispatch(argv)
        finally:
            sys.stdout = old_stdout

    except Exception as e:
        try:
            sys.stdout = old_stdout
        except Exception:
            pass

        result['status'] = 'FAILED'
        result['message'] = 'LinkOS failed: %s' % e
        result['preview'] = buf.getvalue()
        return

    rendered = buf.getvalue()

    result['status'] = 'APPLIED'
    result['message'] = 'LinkOS rendered: %s' % (' '.join(argv) if argv else 'home')
    result['out'] = {'stdout': rendered}
    result['preview'] = rendered
