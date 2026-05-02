# -*- coding: utf-8 -*-
"""
ops.insert_into_ast
===================
Inject code inside an AST target at an anchor line.

Directives:
    ANCHOR      required - substring to find in target body
    POSITION    before|after (default: after)
    INDENT      auto|same|child (default: auto)
                  auto  -> child if anchor ends with ':', else same
                  same  -> match anchor line indent
                  child -> anchor indent + 4 spaces
    MATCH       exact|fuzzy (default: exact)
    OCCURRENCE  N - which match to use (default: 1)
    EXPECT      N - require exactly N matches (default: 1)
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'INSERT_INTO',
    'target_kind': 'ast',
    'body_mode': 'required',
    'allowed_directives': {'ANCHOR', 'POSITION', 'INDENT', 'MATCH', 'OCCURRENCE', 'EXPECT'},
    'required_directives': {'ANCHOR'},
}

# HELP doc block — surfaces via HELP INSERT_INTO.
HELP = {
    'summary': 'Insert new code inside a resolved AST target relative to an anchor line.',
    'subject': [
        'AST target string, for example file.py::Class.method_name.',
        'Use this when you want to inject code without replacing the whole target.',
    ],
    'common_failures': [
        'Missing ANCHOR directive.',
        'Anchor not found or not unique enough.',
        'POSITION must be before or after.',
        'INDENT must be auto, same, or child.',
        'Missing BEGIN_BODY / END_BODY.',
    ],
    'safe_usage': [
        'PREVIEW the target first and use a unique anchor when possible.',
        'Use EXPECT and OCCURRENCE when the anchor may appear more than once.',
        'Use INDENT: child when intentionally inserting under a block header.',
    ],
    'minimal_example': [
        'INSERT_INTO forge_app_lab/forge_app_state.py::build_starter_bundle',
        'ANCHOR: if op == \'READ_FILE\':',
        'POSITION: after',
        'INDENT: child',
        'BEGIN_BODY',
        "if op == 'HELP':",
        "    return 'HELP %s\\n' % subject",
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE', 'APPEND_INTO', 'PREPEND_INTO'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    '_max_hints': 1,
    'anchor': {
        'message': 'INSERT_INTO needs ANCHOR.',
        'why': 'Forge inserts relative to a specific existing line inside the AST target.',
        'priority': 100,
        'example': [
            'INSERT_INTO app.py::main',
            'ANCHOR: existing_line()',
            'POSITION: after',
            'BEGIN_BODY',
            'new_line()',
            'END_BODY',
        ],
        'next': ['PREVIEW the target and copy an exact anchor line', 'HELP INSERT_INTO'],
    },
    'body content': {
        'message': 'INSERT_INTO needs body content.',
        'why': 'Forge needs to know what code to insert at the anchor point.',
        'priority': 100,
        'example': [
            'INSERT_INTO app.py::main',
            'ANCHOR: existing_line()',
            'POSITION: after',
            'BEGIN_BODY',
            'new_line()',
            'END_BODY',
        ],
        'next': ['Add BEGIN_BODY / END_BODY', 'HELP INSERT_INTO'],
    },
    'position': {
        'message': 'INSERT_INTO POSITION must be before or after.',
        'why': 'Forge only supports inserting directly before or after the matched anchor line.',
        'priority': 100,
        'example': [
            'INSERT_INTO app.py::main',
            'ANCHOR: existing_line()',
            'POSITION: after',
            'BEGIN_BODY',
            'new_line()',
            'END_BODY',
        ],
        'next': ['Use POSITION: before or POSITION: after'],
    },
    'indent': {
        'message': 'INSERT_INTO INDENT must be auto, same, or child.',
        'why': 'Indent mode controls how inserted code aligns with the anchor line.',
        'priority': 100,
        'example': [
            'INSERT_INTO app.py::main',
            'ANCHOR: if ready:',
            'POSITION: after',
            'INDENT: child',
            'BEGIN_BODY',
            'do_work()',
            'END_BODY',
        ],
        'next': ['Use INDENT: auto unless you need same or child'],
    },
    'matched 0': {
        'message': 'Anchor text was not found.',
        'why': 'The target may have drifted, or the anchor text was copied inaccurately.',
        'priority': 120,
        'example': [
            'PREVIEW app.py::main',
            '',
            'Then retry with ANCHOR copied from the preview.',
        ],
        'next': ['PREVIEW the target', 'Try MATCH: fuzzy if whitespace differs'],
    },
    'matched 2': {
        'message': 'Anchor text matched more than once.',
        'why': 'Forge cannot safely choose between repeated insertion points.',
        'priority': 120,
        'example': [
            'INSERT_INTO app.py::main',
            'ANCHOR: repeated_line',
            'OCCURRENCE: 2',
            'POSITION: after',
            'BEGIN_BODY',
            'new_line()',
            'END_BODY',
        ],
        'next': ['Use a more specific anchor', 'Use OCCURRENCE: N only when deliberate'],
    },
    'skipped_anchor_mismatch': {
        'message': 'Anchor mismatch: inspect the live target before retrying.',
        'why': 'The code has likely changed since the bundle was written.',
        'priority': 80,
        'example': [
            'PREVIEW app.py::main',
            '',
            'Then retry with current anchor text.',
        ],
        'next': ['PREVIEW the target', 'Tighten the anchor'],
    },
}


def validate(parsed_op):
    """Check target, ANCHOR, and POSITION directives. Returns list of error strings."""
    errors = []
    if not (parsed_op.target or '').strip():
        errors.append('INSERT_INTO requires a target')
    if not parsed_op.body:
        errors.append('INSERT_INTO requires body content')
    if 'ANCHOR' not in parsed_op.directives:
        errors.append('Missing required directive for INSERT_INTO: ANCHOR')
    position = parsed_op.directives.get('POSITION', 'after')
    if position not in ('before', 'after'):
        errors.append('INSERT_INTO POSITION must be before or after, got: ' + str(position))
    indent_mode = parsed_op.directives.get('INDENT', 'auto')
    if indent_mode not in ('auto', 'same', 'child'):
        errors.append('INSERT_INTO INDENT must be auto, same, or child, got: ' + str(indent_mode))
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target, find anchor line, insert body before or after it."""
    from forge.target_resolver import resolve_ast_target
    from forge.source_ops import insert_after_lines, get_line_indent
    from forge.anchor_tools import resolve_single_anchor

    """Resolve AST target, find anchor line, insert body before or after it."""
    resolved = resolve_ast_target(
        ctx.project_root,
        parsed_op.target,
        default_file=parsed_op.default_file,
    )

    if not resolved.get('ok'):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = resolved.get('error') or 'Target not found'
        return

    file_abs = resolved['file_abs']
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    before = resolved['source_text']
    all_lines = before.splitlines()
    start = resolved['start']
    end = resolved['end']
    target_lines = all_lines[start - 1:end]

    match_mode = parsed_op.directives.get('MATCH', 'exact')
    occurrence = parsed_op.directives.get('OCCURRENCE', 1)
    expect = parsed_op.directives.get('EXPECT', 1)

    try:
        occurrence = int(occurrence)
    except Exception:
        occurrence = 1
    try:
        expect = int(expect)
    except Exception:
        expect = 1

    rel_idx, err = resolve_single_anchor(
        target_lines,
        parsed_op.directives.get('ANCHOR', ''),
        match_mode=match_mode,
        occurrence=occurrence,
        expect=expect,
    )
    if err:
        result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
        result['message'] = 'ANCHOR: ' + err
        return

    abs_line = start + rel_idx

    anchor_line = all_lines[abs_line - 1]
    anchor_indent = get_line_indent(anchor_line)

    indent_mode = parsed_op.directives.get('INDENT', 'auto')
    if indent_mode == 'child':
        indent = anchor_indent + '    '
    elif indent_mode == 'same':
        indent = anchor_indent
    else:
        if anchor_line.rstrip().endswith(':'):
            indent = anchor_indent + '    '
        else:
            indent = anchor_indent

    position = parsed_op.directives.get('POSITION', 'after')
    insert_line = abs_line if position == 'after' else abs_line - 1

    after = insert_after_lines(
        before,
        insert_line,
        parsed_op.body,
        indent,
        tight=True,
    )

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = 'inserted %s anchor line %d in %s' % (
        position, abs_line, resolved['kind']
    )
