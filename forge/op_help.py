# -*- coding: utf-8 -*-
"""
op_help.py
==========
Helpers for LIST_OPS and HELP.
"""

from forge.registry import OP_MODULES, OP_SPECS


CATEGORY_LABELS = {
    'inspect': 'Inspect',
    'ast_write': 'AST write',
    'file_write': 'File write',
    'file_manage': 'File manage',
    'run': 'Run / automation',
    'meta': 'Meta',
    'mode': 'Modes',
    'other': 'Other',

}


def _clean_doc_line(text):
    for line in (text or '').splitlines():
        s = line.strip()
        if not s:
            continue
        if set(s) == set('='):
            continue
        if s.startswith('ops.'):
            return ''
        return s.rstrip('.')
    return ''


def _module_by_name():
    out = {}
    for mod in OP_MODULES:
        spec = getattr(mod, 'SPEC', None) or {}
        name = spec.get('name')
        if name:
            out[name] = mod
    return out


def _dedupe_keep_order(items):
    seen = set()
    out = []
    for item in items:
        s = str(item or '').strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _as_directive_set(value):
    """Normalize SPEC directive fields so HELP never crashes on None/dynamic specs."""
    if value is None:
        return set()
    if isinstance(value, set):
        return value
    if isinstance(value, (list, tuple)):
        return set(value)
    if isinstance(value, str):
        return set([value])
    try:
        return set(value)
    except TypeError:
        return set([value])

def _infer_category(op_name, spec):
    """Infer LIST_OPS/HELP category from op semantics, not just body mode."""
    target_kind = spec.get('target_kind')
    body_mode = spec.get('body_mode', 'forbidden')
    name = (op_name or '').upper()

    mutating_prefixes = (
        'REPLACE',
        'INSERT',
        'APPEND',
        'PREPEND',
        'DELETE',
        'MOVE',
        'COPY',
        'CREATE',
        'SET',
    )

    if name in ('LIST_OPS', 'HELP'):
        return 'meta'

    if name in ('EXPLORER', 'BUILDER', 'MEMORY', 'FORGE_AUDIT'):
        return 'mode'

    if name in ('RUN_FILE', 'SHORTCUT', 'CLIPBOARD', 'SUMMARISE'):
        return 'run'
    if name in ('LIST_RUNS', 'REVERT_RUN', 'DIFF'):
        return 'run'

    if name in ('LIST_TARGETS', 'READ_FILE', 'GREP', 'PREVIEW'):
        return 'inspect'

    if target_kind == 'ast':
        if name.startswith(mutating_prefixes) or body_mode in ('required', 'optional'):
            return 'ast_write'
        return 'inspect'

    if target_kind == 'file':
        if name.startswith(('READ', 'PREVIEW', 'LIST', 'GREP')):
            return 'inspect'
        if name.startswith(mutating_prefixes) or body_mode in ('required', 'optional'):
            if name.startswith(('DELETE', 'MOVE', 'COPY')):
                return 'file_manage'
            return 'file_write'
        return 'file_manage'

    return 'other'

def _generic_subject(op_name, spec):
    if op_name == 'LIST_OPS':
        return ['No target.']
    if op_name == 'HELP':
        return ['Registered op name, for example READ_FILE.']

    target_kind = spec.get('target_kind')
    if target_kind == 'file':
        return ['Relative file or directory path inside project root.']
    if target_kind == 'ast':
        return [
            'AST target string, for example file.py::Class.method_name.',
            'Use @name for assignments and Class.* for a whole class.',
        ]
    return ['See op-specific usage.']


def _generic_summary(op_name, spec, mod):
    help_meta = getattr(mod, 'HELP', None) or {}
    if spec.get('summary'):
        return spec['summary']

    if help_meta.get('summary'):
        return help_meta['summary']
    doc_line = _clean_doc_line(getattr(mod, '__doc__', '') or '')
    if doc_line:
        return doc_line
    category = _infer_category(op_name, spec)
    if category == 'inspect':
        return 'Inspect project state.'
    if category == 'ast_write':
        return 'Modify a Python AST target.'
    if category == 'file_write':
        return 'Modify a text file.'
    if category == 'file_manage':
        return 'Manage files or directories.'
    if category == 'run':
        return 'Run or automate a task.'
    if category == 'meta':
        return 'Describe forge capabilities.'
    return 'Forge op.'


def _directive_example(key):
    if key == 'LINES':
        return 'LINES: 12-23'
    if key == 'ANCHOR':
        return 'ANCHOR: substring to match'
    if key == 'ANCHOR_START':
        return 'ANCHOR_START: first marker'
    if key == 'ANCHOR_END':
        return 'ANCHOR_END: second marker'
    if key == 'DEST':
        return 'DEST: path/to/destination'
    if key == 'POSITION':
        return 'POSITION: after'
    if key == 'PATTERN':
        return 'PATTERN: search term'
    if key == 'MATCH':
        return 'MATCH: exact'
    if key == 'FILTER':
        return 'FILTER: .py'
    if key == 'CONTEXT':
        return 'CONTEXT: 3'
    if key == 'INDENT':
        return 'INDENT: auto'
    if key == 'OCCURRENCE':
        return 'OCCURRENCE: 1'
    if key == 'EXPECT':
        return 'EXPECT: 1'
    if key == 'ARGS':
        return 'ARGS: one two'
    if key == 'CONFIRM':
        return 'CONFIRM: yes'
    return key + ': '


def _generic_minimal_example(op_name, spec):
    if op_name == 'LIST_OPS':
        return ['LIST_OPS']
    if op_name == 'HELP':
        return ['HELP READ_FILE']

    target_kind = spec.get('target_kind')
    subject = ''
    if target_kind == 'file':
        subject = ' path/to/file.txt'
    elif target_kind == 'ast':
        subject = ' file.py::MyClass.method_name'

    lines = [op_name + subject]

    required = sorted(_as_directive_set(spec.get('required_directives')))
    for key in required:
        lines.append(_directive_example(key))

    body_mode = spec.get('body_mode', 'forbidden')
    if body_mode == 'required':
        lines.extend([
            'BEGIN_BODY',
            '# replacement content',
            'END_BODY',
        ])
    return lines

def _generic_common_failures(op_name, spec):
    out = []
    if spec.get('target_kind') in ('file', 'ast'):
        out.append('Missing or invalid target.')
    for key in sorted(_as_directive_set(spec.get('required_directives'))):
        out.append('Missing required directive: %s.' % key)
    if spec.get('body_mode') == 'required':
        out.append('Missing BEGIN_BODY / END_BODY.')
    if spec.get('target_kind') == 'file':
        out.append('Absolute or escaping paths are rejected.')
    if spec.get('target_kind') == 'ast':
        out.append('Target must resolve to a real AST target.')
    return out

def _generic_safe_usage(op_name, spec):
    out = []
    category = _infer_category(op_name, spec)
    if category in ('ast_write', 'file_write'):
        out.append('Inspect the target first before writing.')
        out.append('Verify the result after patching.')
    if spec.get('target_kind') == 'file':
        out.append('Use relative paths only.')
    if spec.get('target_kind') == 'ast':
        out.append('Prefer exact target syntax over guessing.')
    return out


def _display_body_mode(spec):
    mode = spec.get('body_mode', 'forbidden')
    if mode == 'none':
        return 'forbidden'
    return mode


def render_ops_list(layer=None):
    modules = _module_by_name()

    def _build_section(filter_layer, label):
        grouped = {}
        for op_name in sorted(OP_SPECS.keys()):
            spec = OP_SPECS.get(op_name, {})
            if spec.get('layer', 'core') != filter_layer:
                continue
            mod = modules.get(op_name)
            category = _infer_category(op_name, spec)
            grouped.setdefault(category, []).append((op_name, _generic_summary(op_name, spec, mod)))

        lines = ['=== FORGE OPS [%s] ===' % label, '']
        for category in ('inspect', 'ast_write', 'file_write', 'file_manage', 'run', 'meta', 'mode', 'other'):

            items = grouped.get(category) or []
            if not items:
                continue
            lines.append(CATEGORY_LABELS.get(category, category))
            for op_name, summary in items:
                lines.append('- %-18s %s' % (op_name, summary))
            lines.append('')
        return '\n'.join(lines).rstrip()

    if layer == 'all':
        core = _build_section('core', 'CORE')
        custom = _build_section('custom', 'CUSTOM')
        return core + '\n\n' + custom + '\n'

        custom = _build_section('custom', 'CUSTOM')
        return core + '\n\n' + custom + '\n'
    elif layer == 'custom':
        return _build_section('custom', 'CUSTOM') + '\n'
    else:
        return _build_section('core', 'CORE') + '\n'

def _render_file_help(rel_path):
    import ast, os
    from forge.registry import OP_SPECS

    # Resolve against project root
    try:
        from forge.config import DOCUMENTS_ROOT
        root = DOCUMENTS_ROOT
    except Exception:
        root = os.path.expanduser('~/Documents')

    abs_path = os.path.join(root, rel_path)
    if not os.path.isfile(abs_path):
        return None

    lines = ['=== FILE HELP ===', 'FILE: ' + rel_path, '']

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
    except Exception:
        docstring = None

    if docstring:
        lines.append(docstring.strip())
    else:
        lines.append('No module docstring found.')
        lines.append('')
        lines.append('Add a docstring at the top of the file to surface help here.')

    return '\n'.join(lines).rstrip() + '\n'

def render_op_help(name_or_path):
    raw = (name_or_path or '').strip()

    # File path branch
    if '/' in raw or raw.endswith('.py'):
        return _render_file_help(raw)

    # Op name branch
    name = raw.upper()
    modules = _module_by_name()
    mod = modules.get(name)
    spec = OP_SPECS.get(name)
    if mod is None or spec is None:
        return None

    help_meta = getattr(mod, 'HELP', None) or {}
    summary = _generic_summary(name, spec, mod)
    subject = help_meta.get('subject') or _generic_subject(name, spec)
    required = sorted(_as_directive_set(spec.get('required_directives')))
    allowed = _as_directive_set(spec.get('allowed_directives'))
    optional = sorted([k for k in allowed if k not in required])
    body_mode = _display_body_mode(spec)
    category = _infer_category(name, spec)

    common_failures = _dedupe_keep_order(
        list(help_meta.get('common_failures') or []) + _generic_common_failures(name, spec)
    )
    safe_usage = _dedupe_keep_order(
        list(help_meta.get('safe_usage') or []) + _generic_safe_usage(name, spec)
    )
    minimal_example = help_meta.get('minimal_example') or _generic_minimal_example(name, spec)
    related_ops = _dedupe_keep_order(help_meta.get('related_ops') or [])

    lines = [
        '=== FORGE2 OP HELP ===',
        'OP: ' + name,
        'KIND: ' + category,
        'SUMMARY: ' + summary,
        '',
        'SUBJECT:',
    ]
    for item in subject:
        lines.append('- ' + item)

    lines.append('')
    lines.append('REQUIRED DIRECTIVES:')
    if required:
        for item in required:
            lines.append('- ' + item)
    else:
        lines.append('- none')

    lines.append('')
    lines.append('OPTIONAL DIRECTIVES:')
    if optional:
        for item in optional:
            lines.append('- ' + item)
    else:
        lines.append('- none')

    lines.append('')
    lines.append('BODY:')
    lines.append('- ' + body_mode)

    lines.append('')
    lines.append('COMMON FAILURES:')
    if common_failures:
        for item in common_failures:
            lines.append('- ' + item)
    else:
        lines.append('- none')

    lines.append('')
    lines.append('SAFE USAGE:')
    if safe_usage:
        for item in safe_usage:
            lines.append('- ' + item)
    else:
        lines.append('- none')

    if related_ops:
        lines.append('')
        lines.append('RELATED OPS:')
        for item in related_ops:
            lines.append('- ' + item)

    lines.append('')
    lines.append('MINIMAL EXAMPLE:')
    for item in minimal_example:
        lines.append(item)

    return '\n'.join(lines).rstrip() + '\n'
