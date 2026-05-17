# -*- coding: utf-8 -*-
"""
forge_core.surface.state
=========================

Persistent navigation memory for the reboot surface.

Surface pages are rendered by separate Pythonista script invocations,
so "back" navigation needs to survive between runs. This module owns
the on-disk state file and the route-stack helpers used by the
dispatcher.

The state file lives at
``forge/artifacts/linkos_state.json`` — isolated
from live LinkOS so a tap in either system doesn't pollute the other's
back stack. It is intentionally small and corruption-tolerant: any
read failure returns an empty dict and any write failure is silently
ignored, because navigation memory must never crash a render.
"""

import json
import os
import time


def _is_forge_home(path):
    path = os.path.abspath(str(path or ''))
    return (
        os.path.isfile(os.path.join(path, 'entry.py'))
        and os.path.isdir(os.path.join(path, 'forge_core'))
        and os.path.isdir(os.path.join(path, 'forge_packages'))
    )


def _forge_home():
    env_home = os.environ.get('FORGE_HOME')
    if env_home and _is_forge_home(env_home):
        return os.path.abspath(env_home)

    cur = os.path.abspath(os.path.dirname(__file__))
    for _ in range(12):
        if _is_forge_home(cur):
            os.environ['FORGE_HOME'] = cur
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    return os.path.abspath(os.path.expanduser('~/Documents'))


STATE_PATH = os.path.join(_forge_home(), 'artifacts', 'linkos_state.json')


def route_to_text(args):
    """Join a route arg list into the canonical text form used in state.

    Empty args resolve to ``'home'`` so the state file always holds a
    real route name.
    """
    return ' '.join(str(a) for a in (args or []) if str(a) != '').strip() or 'home'


def load_state():
    """Return the persisted state dict, or ``{}`` on any failure."""
    try:
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(data):
    """Write the state dict to disk, creating the folder if needed.

    Failures are silent by design — state persistence is a nice-to-have,
    not a hard requirement for rendering.
    """
    try:
        folder = os.path.dirname(STATE_PATH)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except Exception:
        pass


def remember_route(args):
    """Record ``args`` as the new current route.

    The surface is launched as separate Pythonista script invocations,
    so a normal in-memory navigation stack will not survive. Store a
    small route stack on disk instead:

    - ``current`` is the page just rendered.
    - ``stack`` contains earlier pages, newest last.
    - ``previous`` mirrors the top of ``stack`` for older callers/tools.

    The ``back`` route itself is never remembered.
    """
    route = route_to_text(args)
    if route == 'back' or route.startswith('back '):
        return

    state = load_state()
    current = state.get('current') or ''
    stack = state.get('stack') or []
    if not isinstance(stack, list):
        stack = []

    if route == current:
        return

    if current:
        stack.append(current)

    # Keep state tiny and avoid immediate duplicate loops.
    cleaned = []
    for item in stack:
        item = str(item or '').strip()
        if item and (not cleaned or cleaned[-1] != item):
            cleaned.append(item)
    stack = cleaned[-30:]

    state['stack'] = stack
    state['previous'] = stack[-1] if stack else ''
    state['current'] = route
    state['updated_at'] = int(time.time())
    save_state(state)


def previous_route():
    """Pop and return the previous route, defaulting to ``'home'``.

    This mutates the persisted stack so repeated Back taps step through
    history rather than bouncing between the same two routes forever.
    """
    state = load_state()
    stack = state.get('stack') or []
    if not isinstance(stack, list):
        stack = []

    target = ''
    while stack and not target:
        target = str(stack.pop() or '').strip()

    if not target:
        target = str(state.get('previous') or '').strip() or 'home'

    state['current'] = target
    state['stack'] = stack[-30:]
    state['previous'] = state['stack'][-1] if state['stack'] else ''
    state['updated_at'] = int(time.time())
    save_state(state)

    return target
