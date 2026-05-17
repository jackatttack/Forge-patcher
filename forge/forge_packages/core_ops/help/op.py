# -*- coding: utf-8 -*-
"""
HELP reboot op.

Package-native help for package-shaped core ops.

Default mode is rich practical usage context for LLM and user safety.
Quick mode is available when only a compact syntax reminder is wanted.
Full mode preserves the richer package-native view plus package metadata.

Usage:
    HELP SURFACE
    HELP SURFACE full
    HELP SURFACE --full
    HELP SURFACE contract
    HELP
    ARGS: SURFACE
    MODE: full
"""

import importlib.util
import os

from forge_core.registry import OPS_BY_NAME, discover_ops


SPEC = {
    'name': 'HELP',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS', 'MODE']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Show reboot op help. Default is rich practical usage; quick mode is compact.',
    'subject': ['Use same-line args, e.g. HELP LIST_FILES.'],
    'directives': {
        'MODE': 'quick | full | contract. Default: full.',
    },
    'safe_usage': [
        'Use HELP OP for rich usage context while writing bundles.',
        'Use HELP OP quick for a compact syntax reminder.',
        'Use HELP OP contract when debugging package conformance.',
    ],
    'minimal_example': [
        'HELP LIST_FILES',
        'HELP SURFACE full',
        'HELP SURFACE contract',
    ],
}


HINTS = {
    '_max_hints': 1,
    'unknown': {
        'message': 'HELP could not find that op or package.',
        'why': 'The op name may be misspelled, not registered, or newly created in the same still-cached session.',
        'example': [
            'LIST_OPS',
            '',
            'HELP INSERT',
        ],
        'next': [
            'Run LIST_OPS to see registered names.',
            'Use HELP <OP> full only if this entry point supports the mode syntax.',
        ],
    },
}

def validate(parsed_op):
    args = (parsed_op.get('directives') or {}).get('ARGS') or parsed_op.get('target') or ''
    if not args.strip():
        return ['HELP requires an op name']
    return []


def _split_args(raw_args, directives):
    """Return (op_name, mode) from same-line args/directives."""
    raw_args = str(raw_args or '').strip()
    parts = raw_args.split()

    mode = str((directives or {}).get('MODE') or '').strip().lower()
    if not mode:
        mode = 'full'

    mode_aliases = {
        '--full': 'full',
        'full': 'full',
        'detail': 'full',
        'detailed': 'full',
        '--contract': 'contract',
        'contract': 'contract',
        'audit': 'contract',
        'check': 'contract',
        '--quick': 'quick',
        'quick': 'quick',
        'syntax': 'quick',
    }

    if parts and parts[-1].lower() in mode_aliases:
        mode = mode_aliases[parts[-1].lower()]
        parts = parts[:-1]

    if mode in mode_aliases:
        mode = mode_aliases[mode]

    op_name = (parts[0] if parts else raw_args).strip().upper()
    if not op_name and raw_args:
        op_name = raw_args.strip().upper()

    if mode not in ('quick', 'full', 'contract'):
        mode = 'full'

    return op_name, mode


def _load_manifest(folder):
    path = os.path.join(folder, 'manifest.py')
    if not os.path.isfile(path):
        return None, 'missing manifest.py'

    try:
        mod_name = 'forge_reboot_help_manifest_' + os.path.basename(folder)
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        manifest = getattr(mod, 'MANIFEST', None)
        if not isinstance(manifest, dict):
            return None, 'MANIFEST is not a dict'
        return manifest, None
    except Exception as e:
        return None, 'manifest import failed: %s: %s' % (type(e).__name__, e)


def _readme_text(folder):
    path = os.path.join(folder, 'README.txt')
    if not os.path.isfile(path):
        return '', 'missing README.txt'

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read().strip()
    except Exception as e:
        return '', 'README read failed: %s' % e

    return text, None


def _fmt_list(value):
    if value is None:
        return '-'
    if isinstance(value, (list, tuple, set)):
        return ', '.join([str(x) for x in value]) if value else '-'
    return str(value)


def _fmt_directives(value):
    if isinstance(value, dict):
        return ', '.join(sorted(value.keys())) if value else '-'
    if isinstance(value, (list, tuple, set)):
        return ', '.join(sorted([str(x) for x in value])) if value else '-'
    return str(value or '-')


def _contract_status(folder, name, spec, manifest, manifest_error, readme_error, help_data, mod):
    issues = []

    if readme_error:
        issues.append(readme_error)
    if manifest_error:
        issues.append(manifest_error)

    if manifest:
        folder_name = os.path.basename(folder)
        if manifest.get('name') != folder_name:
            issues.append('MANIFEST name mismatch')
        if str(manifest.get('op') or '').upper() != name:
            issues.append('MANIFEST op mismatch')
        for key in ('name', 'op', 'kind', 'version', 'summary'):
            if key not in manifest:
                issues.append('MANIFEST missing ' + key)

    if not isinstance(spec, dict):
        issues.append('missing SPEC dict')
    else:
        for key in ('name', 'target_kind', 'body_mode', 'allowed_directives', 'required_directives'):
            if key not in spec:
                issues.append('SPEC missing ' + key)

    if not isinstance(help_data, dict):
        issues.append('missing HELP dict')
    elif not help_data.get('summary'):
        issues.append('HELP missing summary')

    if not callable(getattr(mod, 'validate', None)):
        issues.append('missing validate()')
    if not callable(getattr(mod, 'execute', None)):
        issues.append('missing execute()')

    return issues


def _summary(name, manifest, help_data):
    if manifest and manifest.get('summary'):
        return str(manifest.get('summary'))
    return str(help_data.get('summary') or '(no summary)')


def _render_quick(name, spec, help_data, manifest, issues):
    lines = []
    lines.append('HELP ' + name)
    lines.append('')
    lines.append(_summary(name, manifest, help_data))

    subject = help_data.get('subject') or []
    if subject:
        lines.append('')
        lines.append('USAGE')
        for item in subject:
            lines.append('- ' + str(item))

    lines.append('')
    lines.append('SPEC')
    lines.append('- target_kind: ' + str(spec.get('target_kind')))
    lines.append('- body_mode: ' + str(spec.get('body_mode')))
    lines.append('- directives: ' + _fmt_directives(spec.get('allowed_directives')))
    lines.append('- required: ' + _fmt_directives(spec.get('required_directives')))

    examples = help_data.get('minimal_example') or []
    if examples:
        lines.append('')
        lines.append('EXAMPLE')
        lines.extend([str(x) for x in examples])

    failures = help_data.get('common_failures') or []
    if failures:
        lines.append('')
        lines.append('GOTCHAS')
        for item in failures[:4]:
            lines.append('- ' + str(item))

    if issues:
        lines.append('')
        lines.append('CONTRACT: FAIL — use HELP %s contract' % name)
    else:
        lines.append('')
        lines.append('CONTRACT: PASS')

    lines.append('')
    lines.append('More: HELP %s full' % name)

    return '\n'.join(lines)


def _render_contract(name, folder, spec, manifest, manifest_error, readme_error, help_data, mod, issues):
    lines = []
    lines.append('HELP ' + name + ' CONTRACT')
    lines.append('')

    if issues:
        lines.append('FAIL')
        for issue in issues:
            lines.append('- ' + str(issue))
    else:
        lines.append('PASS package contract ok')

    lines.append('')
    lines.append('CHECKS')
    lines.append('- folder: ' + os.path.basename(folder))
    lines.append('- README.txt: ' + ('FAIL' if readme_error else 'PASS'))
    lines.append('- manifest.py: ' + ('FAIL' if manifest_error else 'PASS'))
    lines.append('- SPEC: ' + ('PASS' if isinstance(spec, dict) else 'FAIL'))
    lines.append('- HELP: ' + ('PASS' if isinstance(help_data, dict) and help_data.get('summary') else 'FAIL'))
    lines.append('- validate(): ' + ('PASS' if callable(getattr(mod, 'validate', None)) else 'FAIL'))
    lines.append('- execute(): ' + ('PASS' if callable(getattr(mod, 'execute', None)) else 'FAIL'))

    if manifest:
        lines.append('')
        lines.append('MANIFEST')
        for key in sorted(manifest.keys()):
            lines.append('- %s: %s' % (key, manifest.get(key)))

    return '\n'.join(lines)


def _render_full(name, folder, spec, help_data, manifest, manifest_error, readme, readme_error, issues):
    lines = []
    lines.append('HELP ' + name)
    lines.append('')
    lines.append(_summary(name, manifest, help_data))

    if readme:
        lines.append('')
        lines.append('README')
        lines.append(readme)

    lines.append('')
    lines.append('PACKAGE')
    if manifest:
        lines.append('- name: ' + str(manifest.get('name')))
        lines.append('- op: ' + str(manifest.get('op')))
        lines.append('- kind: ' + str(manifest.get('kind')))
        lines.append('- version: ' + str(manifest.get('version')))
        if 'risk' in manifest:
            lines.append('- risk: ' + str(manifest.get('risk')))
        if 'domains' in manifest:
            lines.append('- domains: ' + _fmt_list(manifest.get('domains')))
        if 'provides_pages' in manifest:
            lines.append('- pages: ' + _fmt_list(manifest.get('provides_pages')))
    else:
        lines.append('- ' + str(manifest_error or 'no manifest'))

    lines.append('')
    lines.append('SPEC')
    lines.append('- target_kind: ' + str(spec.get('target_kind')))
    lines.append('- body_mode: ' + str(spec.get('body_mode')))
    lines.append('- directives: ' + _fmt_directives(spec.get('allowed_directives')))
    lines.append('- required: ' + _fmt_directives(spec.get('required_directives')))

    subject = help_data.get('subject') or []
    if subject:
        lines.append('')
        lines.append('SUBJECT')
        for item in subject:
            lines.append('- ' + str(item))

    directives = help_data.get('directives') or {}
    if directives:
        lines.append('')
        lines.append('DIRECTIVES')
        if isinstance(directives, dict):
            for key in sorted(directives.keys()):
                lines.append('- %s: %s' % (key, directives.get(key)))
        else:
            for item in directives:
                lines.append('- ' + str(item))

    safe_usage = help_data.get('safe_usage') or []
    if safe_usage:
        lines.append('')
        lines.append('SAFE USAGE')
        for item in safe_usage:
            lines.append('- ' + str(item))

    failures = help_data.get('common_failures') or []
    if failures:
        lines.append('')
        lines.append('COMMON FAILURES')
        for item in failures:
            lines.append('- ' + str(item))

    examples = help_data.get('minimal_example') or []
    if examples:
        lines.append('')
        lines.append('EXAMPLE')
        lines.extend([str(x) for x in examples])

    related = help_data.get('related_ops') or []
    if related:
        lines.append('')
        lines.append('RELATED')
        lines.append(_fmt_list(related))

    lines.append('')
    lines.append('CONTRACT')
    if issues:
        lines.append('FAIL')
        for issue in issues:
            lines.append('- ' + str(issue))
    else:
        lines.append('PASS package contract ok')

    return '\n'.join(lines)


def execute(ctx, parsed_op, result):
    discover_ops()

    directives = parsed_op.get('directives') or {}
    raw_args = directives.get('ARGS') or parsed_op.get('target') or ''
    name, mode = _split_args(raw_args, directives)

    mod = OPS_BY_NAME.get(name)
    if mod is None:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Unknown op: ' + name
        return

    folder = os.path.dirname(os.path.abspath(getattr(mod, '__file__', '')))
    spec = getattr(mod, 'SPEC', {}) or {}
    help_data = getattr(mod, 'HELP', {}) or {}
    manifest, manifest_error = _load_manifest(folder)
    readme, readme_error = _readme_text(folder)

    issues = _contract_status(folder, name, spec, manifest, manifest_error, readme_error, help_data, mod)

    if mode == 'contract':
        preview = _render_contract(name, folder, spec, manifest, manifest_error, readme_error, help_data, mod, issues)
    elif mode == 'full':
        preview = _render_full(name, folder, spec, help_data, manifest, manifest_error, readme, readme_error, issues)
    else:
        preview = _render_quick(name, spec, help_data, manifest, issues)

    result['status'] = 'APPLIED'
    result['message'] = 'Help for ' + name
    result['preview'] = preview
    result['data'] = {
        'op': name,
        'mode': mode,
        'manifest': manifest or {},
        'contract_issues': issues,
    }
