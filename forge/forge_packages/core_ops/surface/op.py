# -*- coding: utf-8 -*-
"""
SURFACE op.

This controls the user-facing Surface for a run.

It does not execute domain work. It tells the renderer how to shape the page
stack for this run.
"""


SPEC = {
    'name': 'SURFACE',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['TITLE', 'FOCUS', 'STACK', 'HERO', 'MODE']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Set user-facing surface/page-stack intent for this run.',
    'minimal_example': [
        'SURFACE',
        'TITLE: Files and Audit',
        'STACK: files,audit',
        '',
        'LIST_FILES forge',
        'DEPTH: 1',
        'FILES: yes',
        '',
        'SURFACE',
        'TITLE: Patch Review',
        'STACK: summary,audit,raw',
        '',
        'SURFACE',
        'TITLE: Failures Only',
        'STACK: failures,raw',
    ],
}


HINTS = {
    '_max_hints': 2,
    'usage': {
        'message': 'SURFACE shapes the user-facing page stack.',
        'why': 'SURFACE declares which content pages render inline. FOCUS renders one page first. STACK adds selected pages. Summary and audit are normal pages, while bottom navigation controls remain available by default.',
        'example': [
            'SURFACE',
            'TITLE: Files and Audit',
            'STACK: files,audit',
            '',
            'LIST_FILES forge',
            'DEPTH: 1',
        ],
        'next': [
            'Use FOCUS to render a single detailed page.',
            'Use STACK to choose extra inline content pages.',
            'Use STACK: summary or STACK: audit when those pages should appear as content.',
            'Use TITLE to label the surface.',
        ],
    },
    'aliases': {
        'message': 'STACK accepts page ids, aliases, and group tokens.',
        'why': 'Aliases resolve to rich op.detail pages when the matching op ran (files -> LIST_FILES detail, help -> HELP detail, preview -> PREVIEW detail, diff -> DIFF detail). Group tokens expand to multiple pages.',
        'example': [
            'STACK: summary,audit,raw      # render summary and audit as content',
            'STACK: files,audit            # rich LIST_FILES detail + audit as content',
            'STACK: details,raw            # all op detail pages + raw',
            'STACK: failures,audit         # failed/skipped op details only',
            'STACK: writes,audit           # mutating op details only',
            'STACK: reads,audit            # read/search/list op details only',
        ],
        'next': [
            'Core aliases: summary, home, audit, ops, docs, raw, files, help, preview, diff.',
            'Group tokens: details, results, failures, previews, reads, writes.',
            'Aliases with a matching op resolve to the rich op.detail page.',
            'Missing pages are recorded as warnings but do not fail the run.',
        ],
    },
}

def validate(parsed_op):
    return []


def execute(ctx, parsed_op, result):
    directives = parsed_op.get('directives') or {}

    control = {}
    if directives.get('TITLE'):
        control['title'] = directives.get('TITLE')
    if directives.get('FOCUS'):
        control['focus'] = directives.get('FOCUS')
    if directives.get('STACK'):
        control['stack'] = directives.get('STACK')
    if directives.get('HERO'):
        control['hero'] = directives.get('HERO')
    if directives.get('MODE'):
        control['mode'] = directives.get('MODE')

    result['status'] = 'APPLIED'
    result['message'] = 'surface intent set'
    result['surface_control'] = control
    result['data'] = {
        'surface_control': control,
    }
