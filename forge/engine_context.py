# -*- coding: utf-8 -*-
"""
engine_context.py
=================
Shared execution context for engine-run ops.
"""

import os


class EngineContext(object):
    """Shared mutable context passed to every op during a forge run."""
    def __init__(self, project_root, default_file=None):
        """Initialise context with project root, file cache, and touched file registry."""
        self.project_root = os.path.abspath(project_root)
        self.default_file = default_file
        self.file_cache = {}
        self.touched_files = {}
        self.results = []
        self.last_output = ''
        self.last = {}

    def resolve_file(self, target):
        """Resolve a relative path to an absolute path under project root."""
        target = (target or '').strip()
        if os.path.isabs(target):
            return os.path.abspath(target)
        return os.path.abspath(os.path.join(self.project_root, target))

    def in_root(self, file_abs):
        """Return True if absolute path is inside project root."""
        root = os.path.realpath(self.project_root)
        path = os.path.realpath(file_abs)
        return path.startswith(root)
