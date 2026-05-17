# -*- coding: utf-8 -*-
"""
High-level reboot runner.

This is the first proof of the desired architecture:

    text bundle -> parsed ops -> structured run -> packet + Surface output
"""

import os

from forge_core.engine import execute_ops
from forge_core.models import final_status, make_run
from forge_core.parser import parse_bundle
from forge_core.registry import discover_ops
from forge_core.renderers import build_pages, format_packet, format_surface
from forge_core.run_storage import allocate_stamp, write_run


def run_text(bundle_text, project_root=None, mode='dev', store=True):
    if project_root is None:
        project_root = os.path.expanduser('~/Documents')

    discover_ops()

    run = make_run(bundle_text=bundle_text, mode=mode, project_root=project_root)
    run['stamp'] = allocate_stamp(project_root, mode=mode)

    parsed = parse_bundle(bundle_text)
    run['parsed_ops'] = parsed.get('ops') or []
    run['errors'] = parsed.get('errors') or []

    if run['errors']:
        run['results'] = []
    else:
        run['results'] = execute_ops(run['parsed_ops'], project_root, run)

    run['status'] = final_status(run.get('results') or [], run.get('errors') or [])
    run['pages'] = build_pages(run)
    run['packet'] = format_packet(run)
    run['surface_text'] = format_surface(run)

    if store:
        run['artifact_dir'] = write_run(run)

    return run
