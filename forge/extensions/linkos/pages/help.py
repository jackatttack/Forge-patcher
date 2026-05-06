# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.help
===================================

Rendered HELP pages for LinkOS.

This page reads Forge's real op registry and renders each op's SPEC/HELP
metadata through the LinkOS DocPage visual grammar. This keeps LinkOS help
pages aligned with Forge HELP instead of maintaining a separate hand-written
documentation set.
"""

from forge.registry import get_op_module

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_bullets, doc_code, doc_footer, doc_hero, doc_kv,
    doc_section, doc_text,
)


def _as_list(value):
    """Normalise help values to a list of strings."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, set):
        return [str(v) for v in sorted(value) if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _as_directive_set(value):
    """Normalise SPEC directive sets."""
    if value is None:
        return set()
    if isinstance(value, set):
        return set(value)
    if isinstance(value, (list, tuple)):
        return set(value)
    if isinstance(value, str):
        return set([value])
    try:
        return set(value)
    except Exception:
        return set([value])


def _body_label(mode):
    """Human label for a SPEC body mode."""
    mode = str(mode or 'forbidden')
    if mode == 'forbidden':
        return 'forbidden'
    if mode == 'required':
        return 'required'
    if mode == 'optional':
        return 'optional'
    if mode == 'none':
        return 'none'
    return mode


def _target_subject(spec, help_meta):
    """Return subject lines for an op."""
    subject = _as_list(help_meta.get('subject'))
    if subject:
        return subject

    target_kind = spec.get('target_kind')
    if target_kind == 'file':
        return ['Relative file or directory path inside project root.']
    if target_kind == 'ast':
        return [
            'AST target string, for example file.py::Class.method.',
            'Use Class.* for a whole class and @name for assignments.',
        ]
    if target_kind == 'none':
        return ['No subject required.']
    return ['See op-specific usage.']


def _directive_rows(keys, descriptions):
    """Return DocPage key/value rows for directives."""
    rows = []
    descriptions = descriptions or {}
    for key in sorted(keys):
        rows.append((key, descriptions.get(key) or 'Directive accepted by this op.'))
    return rows


def _model_from_op(op):
    """Build a render model from Forge's registered op module."""
    op = str(op or 'HELP').upper()
    mod = get_op_module(op)
    if mod is None:
        return {
            'op': op,
            'kind': 'unknown',
            'summary': 'No registered Forge op was found for this name.',
            'subject': ['Unknown op.'],
            'required': [],
            'optional': [],
            'body': ['unknown'],
            'failures': ['Unknown op name.'],
            'safe': ['Run LIST_OPS all to discover registered ops.'],
            'related': ['HELP', 'LIST_OPS'],
            'example': ['LIST_OPS all'],
            'unknown': True,
        }

    spec = getattr(mod, 'SPEC', None) or {}
    help_meta = getattr(mod, 'HELP', None) or {}

    allowed = _as_directive_set(spec.get('allowed_directives'))
    required = _as_directive_set(spec.get('required_directives'))
    optional = allowed - required
    descriptions = help_meta.get('directives') or {}

    kind = spec.get('target_kind') or 'op'
    layer = spec.get('layer') or getattr(mod, '_layer', '')
    if layer:
        kind = '%s · %s' % (kind, layer)

    summary = (
        help_meta.get('summary')
        or spec.get('summary')
        or 'Forge op.'
    )

    example = _as_list(help_meta.get('minimal_example'))
    if not example:
        example = [op]

    return {
        'op': op,
        'kind': kind,
        'summary': summary,
        'subject': _target_subject(spec, help_meta),
        'required': _directive_rows(required, descriptions),
        'optional': _directive_rows(optional, descriptions),
        'body': [_body_label(spec.get('body_mode'))],
        'failures': _as_list(help_meta.get('common_failures')),
        'safe': _as_list(help_meta.get('safe_usage')),
        'related': _as_list(help_meta.get('related_ops')),
        'example': example,
        'unknown': False,
    }


def _render_related(ops):
    """Render related ops as help links when possible."""
    if not ops:
        return

    doc_section('related')
    for op in ops:
        # Keep this simple for now: related op names render as link-coloured
        # text. Later these can become tappable help links if we add a
        # doc_link primitive.
        doc_text(str(op), tone='accent')


def help_page(op):
    """Render a documentation page for one Forge op."""
    data = _model_from_op(op)
    op = data['op']

    doc_hero(op, data.get('kind') or 'op')
    doc_text(data.get('summary') or '')

    doc_section('subject')
    doc_bullets(data.get('subject') or ['None.'])

    body = data.get('body') or []
    if body:
        doc_section('body')
        doc_bullets(body)

    required = data.get('required') or []
    if required:
        doc_section('required')
        doc_kv(required)

    optional = data.get('optional') or []
    if optional:
        doc_section('optional')
        doc_kv(optional)

    failures = data.get('failures') or []
    if failures:
        doc_section('common failures')
        doc_bullets(failures, tone='muted')

    safe = data.get('safe') or []
    if safe:
        doc_section('safe usage')
        doc_bullets(safe, tone='muted')

    _render_related(data.get('related') or [])

    example = data.get('example') or []
    if example:
        doc_section('example')
        doc_code(example)

    doc_actions([
        ('Copy starter', ('echo', 'copy-starter', op), 'warning', '📋 '),
        ('Related', ('echo', 'related', op), 'accent', '🔗 '),
        ('Raw HELP', ('echo', 'raw-help', op), 'border', '📖 '),
        ('Home', ('home',), 'success', '🏠 '),
    ])

    doc_footer()
