# -*- coding: utf-8 -*-
"""
Package-shaped op registry for the Forge.

Discovers ops from:

    forge_packages/core_ops/<name>/op.py

This intentionally proves package-shaped core ops before we migrate anything
from forge2.
"""

import importlib.util
import os
import sys


OPS_BY_NAME = {}
OP_SPECS = {}
OP_MODULES = []


def _root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ops_root():
    return os.path.join(_root_dir(), 'forge_packages', 'core_ops')


def _load_op_module(path, package_name):
    mod_name = 'forge_reboot_core_op_' + package_name
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        return None, 'could not create import spec'
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod, None


def discover_ops():
    OPS_BY_NAME.clear()
    OP_SPECS.clear()
    OP_MODULES[:] = []

    root = _ops_root()
    if not os.path.isdir(root):
        return

    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name, 'op.py')
        if not os.path.isfile(path):
            continue

        try:
            mod, err = _load_op_module(path, name)
        except Exception as e:
            print('[reboot registry] failed to load %s: %s' % (name, e), file=sys.stderr)
            continue

        if err or mod is None:
            print('[reboot registry] failed to load %s: %s' % (name, err), file=sys.stderr)
            continue

        spec = getattr(mod, 'SPEC', None)
        if not isinstance(spec, dict) or not spec.get('name'):
            print('[reboot registry] %s has no valid SPEC' % name, file=sys.stderr)
            continue

        op_name = str(spec.get('name')).upper()
        OPS_BY_NAME[op_name] = mod
        OP_SPECS[op_name] = spec
        OP_MODULES.append(mod)


def get_op(name):
    if not OPS_BY_NAME:
        discover_ops()
    return OPS_BY_NAME.get(str(name or '').upper())


def get_spec(name):
    if not OP_SPECS:
        discover_ops()
    return OP_SPECS.get(str(name or '').upper())


def list_ops():
    if not OPS_BY_NAME:
        discover_ops()
    return sorted(OPS_BY_NAME.keys())


discover_ops()
