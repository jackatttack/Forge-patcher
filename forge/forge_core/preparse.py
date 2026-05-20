# -*- coding: utf-8 -*-
"""
Pre-parse bundle transforms.

This layer runs before Forge's normal bundle parser. It must stay small,
boring, and explicit because mistakes here affect the language boundary.

Current policy:
- aliases are command shortcuts, not macro expansion inside real bundles
- only a one-line submitted bundle can expand as an alias
- real op names always win
- aliases are loaded from forge/aliases.json
"""

import json
import os
import re


def aliases_path(project_root):
    root = os.path.abspath(project_root or os.path.expanduser('~/Documents'))

    # Normal Forge runs use ~/Documents as project_root, so aliases live at
    # ~/Documents/forge/aliases.json. Smoke tests may run with project_root set
    # directly to the forge/ folder, in which case keep aliases local there.
    if os.path.basename(root.rstrip(os.sep)) == 'forge':
        return os.path.join(root, 'aliases.json')

    return os.path.join(root, 'forge', 'aliases.json')


def load_aliases(project_root):
    path = aliases_path(project_root)
    if not os.path.isfile(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def known_op_names():
    try:
        from forge_core.registry import OPS_BY_NAME, discover_ops
        discover_ops()
        return set(str(k).upper() for k in OPS_BY_NAME.keys())
    except Exception:
        return set()


def alias_entry_parts(entry):
    if isinstance(entry, str):
        return entry, '', [], ''

    if not isinstance(entry, dict):
        return '', '', [], ''

    expansion = str(entry.get('expansion') or '')
    tag = str(entry.get('tag') or '')
    hints = entry.get('args') or []
    if not isinstance(hints, list):
        hints = []
    description = str(entry.get('description') or '')
    return expansion, tag, hints, description


def alias_info_bundle(name):
    return 'ALIAS show %s' % name


def substitute_alias_args(expansion, args_str):
    args_str = str(args_str or '').strip()

    if not args_str:
        if re.search(r'\$\d+', expansion) or '$*' in expansion or '$^' in expansion or '$-1' in expansion:
            raise ValueError('Alias requires arguments but none were supplied.')
        return expansion

    arg_list = args_str.split()
    last_arg = arg_list[-1] if arg_list else ''
    all_but_last = ' '.join(arg_list[:-1])

    out = expansion
    out = out.replace('$*', args_str)
    out = out.replace('$-1', last_arg)
    out = out.replace('$^', all_but_last)

    for idx, arg in enumerate(arg_list, 1):
        out = out.replace('$%d' % idx, arg)

    out = re.sub(r'\$\d+', '', out)
    out = out.replace('$*', '')
    out = out.replace('$^', '')
    out = out.replace('$-1', '')
    return out


def try_expand_alias(bundle_text, project_root):
    stripped = str(bundle_text or '').strip()
    if not stripped:
        return None

    lines = stripped.splitlines()

    # Aliases are command shortcuts, not macro expansion inside real bundles.
    if len(lines) != 1:
        return None

    first_line = lines[0].strip()
    if not first_line:
        return None

    parts = first_line.split(None, 1)
    name = parts[0]
    args_str = parts[1] if len(parts) > 1 else ''

    if name.upper() in known_op_names():
        return None

    aliases = load_aliases(project_root)
    if name not in aliases:
        return None

    expansion, tag, hints, description = alias_entry_parts(aliases.get(name))
    if not expansion.strip():
        return None

    if args_str.strip() in ('?', '??'):
        return alias_info_bundle(name)

    return substitute_alias_args(expansion, args_str)


def expand_bundle(bundle_text, project_root):
    """Return (expanded_text, report).

    report is a small dict suitable for adding to the run object. Empty report
    means no expansion happened.
    """
    expanded = try_expand_alias(bundle_text, project_root)

    if expanded is None:
        return bundle_text, {}

    original = str(bundle_text or '').strip()
    report = {
        'expanded_from_alias': original,
        'expanded_bundle': expanded,
    }
    return expanded, report