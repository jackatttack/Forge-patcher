# -*- coding: utf-8 -*-
"""
ops.prepend_into_ast
====================
Prepend code at start of AST target body.
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'PREPEND_INTO',
    'target_kind': 'ast',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
    'summary': 'Prepend code at the start of a resolved AST target body.',

}

# HELP doc block — surfaces via HELP PREPEND_INTO.
HELP = {
    'summary': 'Prepend code at the start of a resolved AST target body.',
    'subject': [
        'AST target string, for example file.py::Class.method_name.',
        'Best for adding setup code near the top of a function, method, or class body.',
    ],
    'common_failures': [
        'Target does not resolve to a real AST target.',
        'Missing BEGIN_BODY / END_BODY.',
    ],
    'safe_usage': [
        'Use PREVIEW first if you want to confirm where the body begins.',
        'Use this when a simple start-of-body insertion is cleaner than anchor matching.',
    ],
    'minimal_example': [
        'PREPEND_INTO forge_app_lab/forge_app_state.py::build_starter_bundle',
        'BEGIN_BODY',
        "subject = target or file_rel or ''",
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'APPEND_INTO', 'INSERT_INTO'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'body required': 'Provide the code to prepend as the body',
    'not found': 'Target not found — run LIST_TARGETS on the file to see valid targets',
    'ambiguous': 'Target name matched more than once — use file.py::ClassName.method_name to be specific',
}


def validate(parsed_op):
    """Check target and body are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('PREPEND_INTO requires a target')
    if not parsed_op.body:
        errors.append('PREPEND_INTO requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target and prepend body at the start of its block."""
    from forge.target_resolver import resolve_ast_target

    from forge.source_ops import insert_after_lines, get_line_indent

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
    insert_line = resolved['start']
    ref_line = before.splitlines(True)[resolved['start'] - 1]
    indent = get_line_indent(ref_line) + '    '

    patched = insert_after_lines(
        before,
        insert_line,
        parsed_op.body,
        indent,
        tight=True,
    )

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(patched)

    ctx.file_cache[file_abs] = patched
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': patched,
    }

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = 'prepended into %s lines %d-%d' % (
        resolved['kind'],
        resolved['start'],
        resolved['end'],
    )
