# -*- coding: utf-8 -*-
"""
forge.entry
============
Entry point for running forge bundles programmatically.

Thin wrapper around bridge.run_bundle that sets a default project root.
Used by keyboard scripts, the forge app, and any external caller that
wants to run a bundle from text without importing bridge directly.
"""

import os

from forge.bridge import run_bundle


def run_from_text(bundle_text, project_root=None):
    if project_root is None:
        project_root = os.path.expanduser('~/Documents')
    return run_bundle(bundle_text, project_root)
