# -*- coding: utf-8 -*-
"""
forge_reboot.entry
==================

Movable dev entry point for the Forge.

Runs without clipboard by default. This lets us test parser, execution,
structured run data, and rendering directly.
"""

import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))


def _ensure_path():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    if not os.environ.get('FORGE_HOME'):
        os.environ['FORGE_HOME'] = HERE


def _default_project_root():
    return os.path.abspath(
        os.environ.get('FORGE_PROJECT_ROOT')
        or os.path.expanduser('~/Documents')
    )


def run_from_text(bundle_text, project_root=None, mode='dev', store=True):
    _ensure_path()
    from forge_core.runner import run_text
    return run_text(bundle_text, project_root=project_root or _default_project_root(), mode=mode, store=store)


def main():
    _ensure_path()
    from forge_core.runner import run_text

    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            bundle = f.read()
    else:
        bundle = sys.stdin.read()

    run = run_text(bundle, project_root=_default_project_root(), mode='dev', store=True)

    print(run.get('packet') or '')

    # Deliberately print only the packet.
    #
    # The clipboard loop is LLM-facing: stdout becomes the return text the user
    # pastes back into chat. Surface rendering belongs in a separate explicit
    # UI/page action, not appended to every packet as noise.


if __name__ == '__main__':
    main()
