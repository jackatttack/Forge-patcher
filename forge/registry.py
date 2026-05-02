# -*- coding: utf-8 -*-
"""
registry.py
===========
Auto-discovers ops from forge/ops/core/ and forge/ops/custom/.

Layer is inferred from which subpackage the module lives in.
- forge/ops/core/   -> layer='core'
- forge/ops/custom/ -> layer='custom'

To add a core op:   create forge/ops/core/my_op.py with SPEC/validate/execute.
To add a custom op: create forge/ops/custom/my_op.py with SPEC/validate/execute.
Nothing else needed.
"""
import importlib, pkgutil
from forge.config import LOAD_OP_LAYERS

# All loaded op modules in discovery order.
OP_MODULES = []


def _load_layer(layer_name, package_name):
    """Load all op modules from a package and tag them with a layer name."""
    try:
        pkg = importlib.import_module(package_name)
    except Exception as e:
        import sys
        print(f'[registry] WARNING: failed to load op package {package_name!r}: {e}', file=sys.stderr)
        return

    for m in pkgutil.iter_modules(pkg.__path__):
        try:
            mod = importlib.import_module(package_name + '.' + m.name)
            mod._layer = layer_name
            OP_MODULES.append(mod)
        except Exception as e:
            import sys
            print(f'[registry] WARNING: failed to load {layer_name} op {m.name!r}: {e}', file=sys.stderr)


_LAYER_PACKAGES = {
    'core': 'forge.ops.core',
    'custom': 'forge.ops.custom',
}

for _layer in LOAD_OP_LAYERS:
    _pkg_name = _LAYER_PACKAGES.get(_layer)
    if _pkg_name:
        _load_layer(_layer, _pkg_name)
    else:
        import sys
        print(f'[registry] WARNING: unknown op layer {_layer!r}', file=sys.stderr)

# Name -> module and name -> SPEC mappings built from OP_MODULES.
OPS_BY_NAME = {}
# Name -> SPEC dict mapping built from OP_MODULES.
OP_SPECS = {}
for mod in OP_MODULES:
    spec = getattr(mod, 'SPEC', None) or {}
    name = spec.get('name')
    if name:
        spec['layer'] = getattr(mod, '_layer', 'core')
        OPS_BY_NAME[name] = mod
        OP_SPECS[name] = spec

def get_op_module(op_name):
    """Return op module for a given op name, or None if not registered."""
    return OPS_BY_NAME.get(op_name)
