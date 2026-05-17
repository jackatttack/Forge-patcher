# -*- coding: utf-8 -*-
"""
Op-package provider loader for the Surface.

A package may ship a pages.py beside its op.py:

    forge_packages/core_ops/<op_name>/pages.py

That module may expose:

    pages_for_result(result, index, run) -> list[page]
        Inline result pages shown in the run stack.

    render_detail(page, context) -> None
        Full op detail page rendering, used by render_op_detail_page
        when the audit routes to op.detail.N.

Both are optional. Core falls back to generic rendering when absent.
"""

import importlib.util
import os


def _package_name_for_op(op):
    return str(op or '').strip().lower()


def provider_path(run, op):
    root = (run or {}).get('project_root') or os.path.expanduser('~/Documents')
    return os.path.join(
        root,
        'workspaces',
        'forge_reboot',
        'forge_packages',
        'core_ops',
        _package_name_for_op(op),
        'pages.py',
    )


def load_provider(run, op):
    path = provider_path(run, op)
    if not os.path.isfile(path):
        return None

    try:
        mod_name = 'forge_reboot_surface_pages_%s' % _package_name_for_op(op)
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None
