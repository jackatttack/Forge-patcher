# -*- coding: utf-8 -*-
"""
compat_normalizer.py
====================

Conservative compatibility normalisation for common LLM Forge syntax misses.

Policy:
- Normalise only surface syntax, not vague intent.
- Only apply deterministic rewrites.
- Keep the strict parser/validator as the source of truth after normalisation.
"""

import re


def _is_op_header(stripped):
    """Return True for simple Forge op header lines."""
    if not stripped:
        return False
    if ':' in stripped:
        return False
    if stripped in ('BEGIN_BODY', 'END_BODY', 'BEGIN_OLD', 'END_OLD', 'BEGIN_NEW', 'END_NEW'):
        return False
    return re.match(r'^[A-Z_][A-Z0-9_]*(\s|$)', stripped) is not None


def _op_name_from_header(stripped):
    """Return the leading op name from an op header line."""
    return (stripped.split(None, 1)[0] or '').upper()


def _normalise_directive_line(line):
    """Normalise a single directive-ish line."""
    raw = line.rstrip('\n')
    stripped = raw.strip()

    if not stripped:
        return raw, None

    leading = raw[:len(raw) - len(raw.lstrip())]

    if re.match(r'^ARG\s*:', stripped):
        value = stripped.split(':', 1)[1].strip()
        return leading + 'ARGS: ' + value, 'ARG -> ARGS'

    m = re.match(r'^ARG\s+(.+)$', stripped)
    if m and ':' not in stripped:
        return leading + 'ARGS: ' + m.group(1).strip(), 'ARG <value> -> ARGS: <value>'

    m = re.match(r'^ARGS\s+(.+)$', stripped)
    if m and ':' not in stripped:
        return leading + 'ARGS: ' + m.group(1).strip(), 'ARGS <value> -> ARGS: <value>'

    if re.match(r'^LINE\s*:', stripped):
        value = stripped.split(':', 1)[1].strip()
        return leading + 'LINES: ' + value, 'LINE -> LINES'

    m = re.match(r'^LINE\s+(.+)$', stripped)
    if m and ':' not in stripped:
        return leading + 'LINES: ' + m.group(1).strip(), 'LINE <value> -> LINES: <value>'

    m = re.match(r'^LINES\s+(.+)$', stripped)
    if m and ':' not in stripped:
        return leading + 'LINES: ' + m.group(1).strip(), 'LINES <value> -> LINES: <value>'

    return raw, None


def _range_directive(stripped):
    """Return (key, value) for START:/END:/LINES: style range directives."""
    m = re.match(r'^(START|END|LINES)\s*:\s*(.*)$', stripped)
    if not m:
        return None, None
    return m.group(1).upper(), m.group(2).strip()


def _directive_value(stripped, key):
    """Return directive value for KEY:, or None if the line is not that directive."""
    pattern = r'^%s\s*:\s*(.*)$' % re.escape(key)
    m = re.match(pattern, stripped or '', flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def _normalise_insert_anchor_blocks(text):
    """Rewrite INSERT_AFTER/INSERT_BEFORE + ANCHOR into INSERT_INTO.

    INSERT_AFTER and INSERT_BEFORE are sibling AST insertion ops. When a model
    supplies ANCHOR with them, the intent is not sibling insertion anymore; it is
    anchored insertion inside the target. INSERT_INTO already owns that semantic,
    so this normaliser only rewrites the surface syntax.
    """
    if not text:
        return text, []

    lines = text.splitlines()
    out = []
    notes = []
    seen = set()
    suffix = '\n' if text.endswith('\n') else ''

    def add_note(note):
        if note and note not in seen:
            notes.append(note)
            seen.add(note)

    def looks_like_op_header(stripped):
        """Header detection for the pre-pass.

        This intentionally allows AST targets containing ::. Directive lines such
        as ANCHOR: do not match because the first token is followed by ':' rather
        than whitespace/end.
        """
        if not stripped:
            return False
        if stripped in ('BEGIN_BODY', 'END_BODY', 'BEGIN_OLD', 'END_OLD', 'BEGIN_NEW', 'END_NEW'):
            return False
        return re.match(r'^[A-Z_][A-Z0-9_]*(\s|$)', stripped) is not None

    def insert_header(stripped):
        """Return (op, target) for INSERT_AFTER/BEFORE headers."""
        m = re.match(r'^(INSERT_AFTER|INSERT_BEFORE)(?:\s+(.*))?$', stripped or '')
        if not m:
            return None, ''
        return m.group(1), (m.group(2) or '').strip()

    def block_has_anchor(block):
        in_body = False
        for raw in block[1:]:
            stripped = raw.strip()
            if stripped == 'BEGIN_BODY':
                in_body = True
                continue
            if stripped == 'END_BODY':
                in_body = False
                continue
            if not in_body and _directive_value(stripped, 'ANCHOR') is not None:
                return True
        return False

    def transform_block(block, op, target):
        position = 'after' if op == 'INSERT_AFTER' else 'before'
        header_indent = block[0][:len(block[0]) - len(block[0].lstrip())]
        new_block = [header_indent + 'INSERT_INTO ' + target]

        in_body = False
        inserted_position = False

        for raw in block[1:]:
            stripped = raw.strip()

            if stripped == 'BEGIN_BODY':
                in_body = True
                new_block.append(raw)
                continue

            if stripped == 'END_BODY':
                in_body = False
                new_block.append(raw)
                continue

            if not in_body and _directive_value(stripped, 'POSITION') is not None:
                # The original op name is the clearer signal, so discard any
                # conflicting POSITION supplied beside INSERT_AFTER/BEFORE.
                continue

            new_block.append(raw)

            if not in_body and _directive_value(stripped, 'ANCHOR') is not None and not inserted_position:
                indent = raw[:len(raw) - len(raw.lstrip())]
                new_block.append(indent + 'POSITION: ' + position)
                inserted_position = True

        if not inserted_position:
            new_block.insert(1, 'POSITION: ' + position)

        add_note('%s ANCHOR -> INSERT_INTO POSITION %s' % (op, position))
        return new_block

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        op, target = insert_header(stripped)
        if op not in ('INSERT_AFTER', 'INSERT_BEFORE'):
            out.append(raw)
            i += 1
            continue

        if not target:
            out.append(raw)
            i += 1
            continue

        block = [raw]
        i += 1
        in_body = False

        while i < len(lines):
            candidate = lines[i]
            candidate_stripped = candidate.strip()

            if not in_body and looks_like_op_header(candidate_stripped):
                break

            block.append(candidate)

            if candidate_stripped == 'BEGIN_BODY':
                in_body = True
            elif candidate_stripped == 'END_BODY':
                in_body = False

            i += 1

        if block_has_anchor(block):
            out.extend(transform_block(block, op, target))
        else:
            out.extend(block)

    return '\n'.join(out) + suffix, notes

def normalise_bundle(text):
    """Return (normalised_text, notes)."""
    if not text:
        return text, []

    text, pre_notes = _normalise_insert_anchor_blocks(text)

    out = []
    notes = []
    seen = set()

    for note in pre_notes:
        if note and note not in seen:
            notes.append(note)
            seen.add(note)

    current_op = None
    in_body = False
    pending_start = None
    pending_end = None
    pending_lines = []
    pending_has_lines = False

    def add_note(note):
        if note and note not in seen:
            notes.append(note)
            seen.add(note)

    def flush_pending_range():
        nonlocal pending_start, pending_end, pending_lines, pending_has_lines

        if current_op == 'REPLACE_FILE_RANGE':
            if pending_start and pending_end and not pending_has_lines:
                indent = pending_start[0]
                out.append(indent + 'LINES: ' + pending_start[1] + '-' + pending_end[1])
                add_note('REPLACE_FILE_RANGE START/END -> LINES')
            else:
                for raw_line in pending_lines:
                    out.append(raw_line)
        else:
            for raw_line in pending_lines:
                out.append(raw_line)

        pending_start = None
        pending_end = None
        pending_lines = []
        pending_has_lines = False

    for line in text.splitlines():
        raw = line.rstrip('\n')
        stripped = raw.strip()
        leading = raw[:len(raw) - len(raw.lstrip())]

        if stripped == 'BEGIN_BODY':
            flush_pending_range()
            in_body = True
            out.append(raw)
            continue

        if stripped == 'END_BODY':
            flush_pending_range()
            in_body = False
            out.append(raw)
            continue

        if not in_body and _is_op_header(stripped):
            flush_pending_range()
            current_op = _op_name_from_header(stripped)
            out.append(raw)
            continue

        if not in_body and current_op == 'REPLACE_FILE_RANGE':
            key, value = _range_directive(stripped)
            if key in ('START', 'END', 'LINES'):
                if key == 'START':
                    pending_start = (leading, value)
                    pending_lines.append(raw)
                    continue
                if key == 'END':
                    pending_end = (leading, value)
                    pending_lines.append(raw)
                    continue
                if key == 'LINES':
                    pending_has_lines = True
                    pending_lines.append(raw)
                    continue

        flush_pending_range()
        new_line, note = _normalise_directive_line(raw)
        out.append(new_line)
        add_note(note)

    flush_pending_range()

    suffix = '\n' if text.endswith('\n') else ''
    return '\n'.join(out) + suffix, notes
