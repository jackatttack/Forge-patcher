# -*- coding: utf-8 -*-
"""
refresh
=======
Best-effort Forge module cache refresh for Pythonista.

This op is designed for the common pain point where an op file has changed on
disk but Pythonista is still using an already-imported module.

Limitations:
- REFRESH cannot make a brand-new op available inside the same already-parsed
  bundle. Restart once after creating this file.
- REFRESH is best for edited existing ops, HELP docs, HINTS, and registry/list
  surfaces.
- Parser/engine/bridge changes may still need a full Pythonista restart.
"""

SPEC = {
    'name': 'REFRESH',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Best-effort reload of Forge op modules and registry to reduce Pythonista module-cache pain.',
    'subject': ['No subject. Optional ARGS may be all, ops, or help. Default is all.'],
    'common_failures': [
        'New ops are not available until the parser has seen them; restart once after creating new op files.',
        'Syntax errors in an op module can prevent that module from reloading.',
        'Parser, engine, bridge, and shortcut changes may still require a full restart.',
    ],
    'safe_usage': [
        'Run after editing an existing op file, HELP dict, HINTS dict, or op_help.py.',
        'Run before retrying HELP or LIST_OPS when output appears stale.',
        'Still restart Pythonista after structural changes to parser, engine, bridge, or newly-created ops.',
    ],
    'related_ops': ['HELP', 'LIST_OPS', 'FORGE_AUDIT', 'GUIDE'],
    'minimal_example': [
        'REFRESH',
        '',
        'REFRESH',
        'ARGS: ops',
    ],
}

HINTS = {
    'syntax': 'A reloaded module may have a syntax/import error; PREVIEW the edited file and fix it.',
    'new op': 'Brand-new ops still need one restart before the parser can recognise them.',
}


def validate(parsed_op):
    """REFRESH accepts optional ARGS only."""
    return []


def _reload_module(name, reloaded, failed):
    import importlib
    import sys

    mod = sys.modules.get(name)
    if mod is None:
        return None
    try:
        new_mod = importlib.reload(mod)
        reloaded.append(name)
        return new_mod
    except Exception as e:
        failed.append('%s: %s: %s' % (name, type(e).__name__, e))
        return mod


def _rebuild_registry(registry_mod, reloaded, failed):
    """Repopulate the existing registry module globals in-place."""
    import importlib
    import pkgutil
    from forge.config import LOAD_OP_LAYERS

    registry_mod.OP_MODULES[:] = []
    registry_mod.OPS_BY_NAME.clear()
    registry_mod.OP_SPECS.clear()

    layer_packages = {
        'core': 'forge.ops.core',
        'custom': 'forge.ops.custom',
    }

    for layer in LOAD_OP_LAYERS:
        pkg_name = layer_packages.get(layer)
        if not pkg_name:
            failed.append('unknown op layer: %s' % layer)
            continue

        try:
            pkg = importlib.import_module(pkg_name)
        except Exception as e:
            failed.append('%s: %s: %s' % (pkg_name, type(e).__name__, e))
            continue

        for item in pkgutil.iter_modules(pkg.__path__):
            mod_name = pkg_name + '.' + item.name
            try:
                mod = importlib.import_module(mod_name)
                mod = importlib.reload(mod)
                mod._layer = layer
                registry_mod.OP_MODULES.append(mod)
                reloaded.append(mod_name)
            except Exception as e:
                failed.append('%s: %s: %s' % (mod_name, type(e).__name__, e))

    for mod in registry_mod.OP_MODULES:
        spec = getattr(mod, 'SPEC', None) or {}
        name = spec.get('name')
        if name:
            spec['layer'] = getattr(mod, '_layer', 'core')
            registry_mod.OPS_BY_NAME[name] = mod
            registry_mod.OP_SPECS[name] = spec


def execute(ctx, parsed_op, result):
    """Refresh Forge modules in-place where possible."""
    import importlib
    import sys

    mode = (parsed_op.directives.get('ARGS') or 'all').strip().lower()
    reloaded = []
    failed = []
    notes = []

    importlib.invalidate_caches()
    # Config and run-storage paths are runtime surface too. Reload these before
    # rebuilding the registry so LOAD_OP_LAYERS and RUNS_DIRNAME changes apply.
    for module_name in ('forge.config', 'forge.run_storage'):
        _reload_module(module_name, reloaded, failed)

    registry_mod = sys.modules.get('forge.registry')
    if registry_mod is None:
        try:
            import forge.registry as registry_mod
        except Exception as e:
            result['status'] = 'FAILED'
            result['message'] = 'REFRESH failed importing registry: %s: %s' % (type(e).__name__, e)
            return

    if mode in ('all', 'ops'):
        _rebuild_registry(registry_mod, reloaded, failed)

        # Update already-imported parser/op_help modules so they see the refreshed
        # OP_SPECS object from the in-place registry.
        parser_mod = sys.modules.get('forge.parser_main')
        if parser_mod is not None:
            try:
                parser_mod.OP_SPECS = registry_mod.OP_SPECS
                notes.append('parser_main.OP_SPECS rebound')
            except Exception as e:
                failed.append('forge.parser_main bind: %s: %s' % (type(e).__name__, e))

        op_help_mod = sys.modules.get('forge.op_help')
        if op_help_mod is not None:
            try:
                op_help_mod.OP_MODULES = registry_mod.OP_MODULES
                op_help_mod.OP_SPECS = registry_mod.OP_SPECS
                _reload_module('forge.op_help', reloaded, failed)
            except Exception as e:
                failed.append('forge.op_help bind: %s: %s' % (type(e).__name__, e))

    elif mode == 'help':
        _reload_module('forge.op_help', reloaded, failed)

    else:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'REFRESH unknown mode: %s. Use all, ops, or help.' % mode
        return

    lines = []
    lines.append('=== REFRESH ===')
    lines.append('mode=%s' % mode)
    lines.append('reloaded=%d failed=%d notes=%d' % (len(reloaded), len(failed), len(notes)))
    lines.append('')
    lines.append('NOTES:')
    if notes:
        for item in notes:
            lines.append('- ' + item)
    else:
        lines.append('- none')
    lines.append('')
    lines.append('FAILED:')
    if failed:
        for item in failed:
            lines.append('- ' + item)
    else:
        lines.append('- none')
    lines.append('')
    lines.append('REMINDER:')
    lines.append('- New ops still need one restart before parser recognition.')
    lines.append('- Parser/engine/bridge/shortcut edits may still need a full Pythonista restart.')

    result['status'] = 'APPLIED' if not failed else 'FAILED'
    result['message'] = 'Forge refresh complete' if not failed else 'Forge refresh completed with failures'
    result['preview'] = '\n'.join(lines).rstrip() + '\n'
