# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.help
===================================

Rendered HELP pages for LinkOS.

This page reads Forge's real op registry and renders each op's SPEC/HELP
metadata through the LinkOS DocPage visual grammar.

It also owns human-facing public help topics such as install, buttons,
module-not-found, run-missing, root, and start-here. Those topics are the
LinkOS version of the HELP lifeboat.
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
    """Render related ops as simple text links for now."""
    if not ops:
        return

    doc_section('related')
    for op in ops:
        doc_text(str(op), tone='accent')


def _common_actions():
    return [
        ('Start Here', ('start-here',), 'success', '🧭 '),
        ('Health', ('install-health',), 'warning', '🩺 '),
        ('Docs', ('docs',), 'accent', '📖 '),
        ('Home', ('home',), 'success', '🏠 '),
    ]


def _topic_model(topic):
    """Return a human-facing help model for non-op topics."""
    key = str(topic or '').strip().lower().replace('_', '-')

    topics = {
        'install': {
            'title': 'Install',
            'subtitle': 'get Forge running',
            'summary': 'Use the public installer for the easiest setup, or install manually from the repo.',
            'sections': [
                ('quick install', [
                    'Create a new Pythonista file named install_forge.py.',
                    'Paste the installer script from the public repo.',
                    'Run it.',
                    'It installs Forge into ~/Documents/Forge.',
                ]),
                ('after install', [
                    'Open Forge/forge_entry.py.',
                    'Run it once.',
                    'LinkOS should render at the bottom of the console.',
                    'Open root AI_FIRST_BOOT.txt and paste it into an LLM.',
                ]),
                ('safe default', [
                    'Contained mode is the safe default.',
                    'Root launcher mode is optional and can be enabled later with install_root_router.py.',
                ]),
            ],
        },
        'run-missing': {
            'title': 'Run Missing',
            'subtitle': 'visual run page could not load',
            'summary': 'RUN MISSING means LinkOS could not find saved visual run details for a run.',
            'sections': [
                ('what it means', [
                    'The Forge packet above may still be valid.',
                    'This usually means the run manifest was not found, not that the whole bundle failed.',
                ]),
                ('safe checks', [
                    'Run HELP HELP to check Forge itself.',
                    'Run start_here.py if you are unsure.',
                    'Run install_health.py if imports or launchers seem wrong.',
                ]),
            ],
        },
        'module-not-found': {
            'title': 'Module Not Found',
            'subtitle': 'import recovery',
            'summary': 'ModuleNotFoundError usually means Pythonista imported the wrong package, cached stale modules, or a file is missing.',
            'sections': [
                ('safe recovery', [
                    'Fully close Pythonista from the app switcher.',
                    'Reopen Pythonista.',
                    'Run install_health.py.',
                    'Check whether a lowercase ~/Documents/forge folder is shadowing ~/Documents/Forge/forge.',
                ]),
            ],
        },
        'buttons': {
            'title': 'Buttons',
            'subtitle': 'LinkOS taps',
            'summary': 'If LinkOS renders but buttons do not tap, you are probably in contained mode.',
            'sections': [
                ('what to do', [
                    'This is not a broken install.',
                    'Run forge_entry.py manually.',
                    'For tappable buttons, install optional root launcher mode with install_root_router.py.',
                ]),
            ],
        },
        'root': {
            'title': 'Root Mode',
            'subtitle': 'optional power',
            'summary': 'Root launcher mode is optional. It enables tappable LinkOS buttons and wider workspace access.',
            'sections': [
                ('benefits', [
                    'Tappable LinkOS console links.',
                    'Easier Shortcut setup.',
                    'Wider Pythonista Documents workspace access.',
                ]),
                ('risk', [
                    'Forge can inspect and patch more files.',
                    'Only enable it deliberately.',
                    'Keep trusting the run packet and inspect before editing.',
                ]),
            ],
        },
        'root-launcher-mode': {
            'title': 'Root Mode',
            'subtitle': 'optional power',
            'summary': 'Root launcher mode is optional. It enables tappable LinkOS buttons and wider workspace access.',
            'sections': [
                ('how to enable', [
                    'Run install_root_router.py from the Forge install folder.',
                    'It writes root forge_entry.py and linkos.py launchers.',
                    'Existing launchers are backed up first.',
                ]),
                ('risk', [
                    'Forge can inspect and patch more files.',
                    'Only enable it deliberately.',
                ]),
            ],
        },
        'start-here': {
            'title': 'Start Here',
            'subtitle': 'safe orientation',
            'summary': 'Start Here is the public Forge lifeboat. It explains what Forge is and what to do next.',
            'sections': [
                ('first safe path', [
                    'Run forge_entry.py once.',
                    'Open root AI_FIRST_BOOT.txt and paste it into an LLM.',
                    'Copy the small bundle the LLM gives you.',
                    'Run forge_entry.py again and paste the packet back.',
                ]),
            ],
        },
        'where-am-i': {
            'title': 'Where Am I?',
            'subtitle': 'orientation',
            'summary': 'Use this when Forge opens but you are unsure what mode, folder, or install state you are in.',
            'sections': [
                ('safe checks', [
                    'Run install_health.py.',
                    'Run start_here.py.',
                    'Run HELP HELP.',
                    'Use LIST_FILES . in a bundle to see the active Forge root.',
                ]),
            ],
        },
    }

    return topics.get(key)


def _render_topic_help(topic):
    """Render a human-facing topic page."""
    model = _topic_model(topic)
    if not model:
        return False

    doc_hero(model['title'], model.get('subtitle') or 'help')
    doc_text(model.get('summary') or '')

    for title, lines in model.get('sections') or []:
        doc_section(title)
        doc_bullets(lines)

    doc_actions(_common_actions())
    doc_footer()
    return True


def help_page(op):
    """Render a human topic page or documentation page for one Forge op."""
    if _render_topic_help(op):
        return

    data = _model_from_op(op)
    op = data['op']

    if data.get('unknown'):
        doc_hero(op, 'unknown')
        doc_text('No registered Forge op or human help topic was found for this name.', tone='warning')
        doc_text('Try Start Here, Health, Docs, or one of the common help topics below.', tone='muted')
        doc_actions([
            ('Start Here', ('start-here',), 'success', '🧭 '),
            ('Install', ('help', 'install'), 'warning', '📥 '),
            ('Run missing', ('help', 'run-missing'), 'orange', '◎ '),
            ('Buttons', ('help', 'buttons'), 'accent', '🔘 '),
            ('Root mode', ('help', 'root'), 'border', '🧭 '),
            ('Home', ('home',), 'success', '🏠 '),
        ])
        doc_footer()
        return

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

    doc_actions(_common_actions())
    doc_footer()
