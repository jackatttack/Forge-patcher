# -*- coding: utf-8 -*-
"""
ops.replace_ast
===============
REPLACE op — wholesale replacement of an AST target.

Resolves a named function, method, class, or assignment by AST target
syntax (file.py::Class.method) and replaces its entire line range with
the supplied body. Safer than anchor-based ops for large or messy targets
since it rewrites the whole thing cleanly.
"""

from forge.target_resolver import resolve_ast_target
from forge.source_ops import replace_line_range

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE',
    'target_kind': 'ast',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP REPLACE.
HELP = {
    'summary': 'Replace an entire resolved AST target such as a method, function, class, or assignment.',
    'body': [
        'Wrap replacement code in BEGIN_BODY / END_BODY.',
        'The body must include the full def or assignment — do not omit the signature.',
    ],
    'subject': [
        'AST target string, for example file.py::Class.method_name.',
        'Use @name for assignments and Class.* for a whole class.',
    ],
    'common_failures': [
        'Target does not resolve to a real AST target.',
        'Missing BEGIN_BODY / END_BODY — always required.',
        'Attempting to patch loose top-level code that is not an AST target.',
    ],
    'safe_usage': [
        'Prefer this over anchor-based AST edits when replacing a whole target.',
        'Use PREVIEW first if current content may have drifted.',
        'This is usually the safest AST write op for large edits.',
    ],
    'minimal_example': [
        'REPLACE forge_app_lab/forge_app_state.py::build_starter_bundle',
        'BEGIN_BODY',
        'def build_starter_bundle(op_name, file_rel=None, target=None):',
        "    return '%s %s\\n' % (op_name, target or file_rel or '')",
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE_LINE', 'REPLACE_LINES', 'INSERT_INTO'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'body required': 'Provide the full replacement function or class as the body',
    'not found': 'Target not found — run LIST_TARGETS on the file to see valid targets',
    'ambiguous': 'Target name matched more than once — use file.py::ClassName.method_name to be specific',
}


def validate(parsed_op):
    """Check that target and body are both present. Returns list of error strings."""
    errors = []
    if not (parsed_op.target or '').strip():
        errors.append('REPLACE requires a target')
    if not parsed_op.body:
        errors.append('REPLACE requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target, replace its line range with body, write file, update cache."""
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
    after = replace_line_range(
        before,
        resolved['start'],
        resolved['end'],
        parsed_op.body,
    )

    if after == before:
        result['file'] = resolved['file_ref']
        result['status'] = 'SKIPPED_ALREADY_APPLIED'
        result['message'] = '%s lines %d-%d unchanged' % (
            resolved['kind'],
            resolved['start'],
            resolved['end'],
        )
        return

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = '%s lines %d-%d replaced' % (
        resolved['kind'],
        resolved['start'],
        resolved['end'],
    )
