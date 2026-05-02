# -*- coding: utf-8 -*-
"""
core_guard.py
=============

Safety guard for edits to Forge's own execution core.

The rule is deliberately simple:
- Mutating ops that target core Forge files require CONFIRM: yes.
- The guard blocks before execution and tells the model to branch first.
"""

CORE_FILES = set([
    'forge/bridge.py',
    'forge/parser_main.py',
    'forge/engine.py',
    'forge/registry.py',
    'forge/run_packet.py',
    'forge/validators.py',
    'forge/entry.py',
    'forge_entry.py',
])

MUTATING_OP_PREFIXES = (
    'REPLACE',
    'INSERT',
    'APPEND',
    'PREPEND',
    'CREATE',
    'DELETE',
    'MOVE',
    'COPY',
    'SET',
)


def _clean_path(target):
    """Extract a file-ish path from a Forge target."""
    target = (target or '').strip()
    if not target:
        return ''

    # AST targets look like path.py::Class.method
    if '::' in target:
        target = target.split('::', 1)[0].strip()

    return target.lstrip('./')


def is_mutating_op(op_name):
    """Return True if the op is a write/manage style op."""
    op = (op_name or '').upper()
    return op.startswith(MUTATING_OP_PREFIXES)


def is_core_path(path):
    """Return True if path is one of the protected Forge core files."""
    clean = _clean_path(path)
    return clean in CORE_FILES


def needs_confirm(parsed_op):
    """Return True if this parsed op targets protected Forge core."""
    if not is_mutating_op(parsed_op.op):
        return False
    return is_core_path(parsed_op.target)


def has_confirm(parsed_op):
    """Return True if CONFIRM: yes is present."""
    value = (parsed_op.directives.get('CONFIRM') or '').strip().lower()
    return value in ('yes', 'y', 'true', '1')


def guard_message(parsed_op):
    """Return a clear blocking message for a protected core edit."""
    target = _clean_path(parsed_op.target)
    lines = [
        "Core Forge file edit blocked: %s" % target,
        "WHY: This target is part of Forge's parser/execution/shortcut core.",
        "REQUIRED:",
        "- Create a BRANCH before touching core files.",
        "- Add CONFIRM: yes to the core-editing op.",
        "- Keep the core patch isolated from unrelated app work.",
        "- Prefer whole-function replacement over fragile line-range edits inside nested control flow.",
        "- Run a smoke test immediately after patching.",
        "SAFE PATTERN:",
        "BRANCH create before_core_change",
        "BEGIN_BODY",
        target,
        "END_BODY",
        "",
        "<your core-editing op>",
        "CONFIRM: yes",
        "<same required directives/body as normal>",
        "",
        "SMOKE TEST:",
        "RUN_FILE forge/entry.py",
        "",
        "NEXT:",
        "- Re-run only after a branch exists.",
        "- Keep the batch small.",
        "- Do not combine core edits with unrelated app work.",
    ]
    return "\n".join(lines)
