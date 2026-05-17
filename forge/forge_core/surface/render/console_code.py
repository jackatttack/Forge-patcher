# -*- coding: utf-8 -*-
"""
forge_core.surface.render.console_code
=======================================

Console-native syntax highlighting for code/output blocks.

Separate from any WebView/HTML code renderer. Surface renders into the
Pythonista console, so highlighting is done by printing small coloured
chunks.

Palette rule:
- red    = Python keywords and builtins
- green  = names, functions, attributes, modules
- yellow = strings, docstrings, comments, numbers
- white  = punctuation/plain text
- muted  = line numbers

No cyan/blue is used for Python syntax tokens.
"""

import re
import token
import tokenize
import io

from forge_core.surface.render.primitives import colour, reset


LINE_NO_RE = re.compile(r'^(\s*)(\d{3,5}:)(.*)$')

PY_KEYWORDS = set([
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
    'except', 'finally', 'for', 'from', 'global', 'if', 'import',
    'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
    'return', 'try', 'while', 'with', 'yield',
])

PY_BUILTINS = set([
    'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
    'set', 'tuple', 'open', 'bool', 'enumerate', 'zip', 'min', 'max',
    'sum', 'abs', 'isinstance', 'getattr', 'setattr', 'hasattr',
    'super', 'object', 'Exception', 'ValueError', 'TypeError',
    'OSError', 'RuntimeError', 'ImportError', 'IndexError',
])

TOKEN_RE = re.compile(
    r'("""|\'\'\')'
    r'|("(?:\\.|[^"\\])*"?)'
    r"|('(?:\\.|[^'\\])*'?)"
    r'|\b[A-Za-z_][A-Za-z0-9_]*\b'
    r'|\b\d+(?:\.\d+)?\b'
    r'|==|!=|<=|>=|:=|->|\+=|-=|\*=|/=|//=|\*\*'
    r'|[+\-*/%=<>!&|^~:.,()[\]{}]'
)


def _write(text, tone='text'):
    """Write a coloured chunk without adding a newline."""
    if not text:
        return
    colour(tone)
    print(str(text), end='')
    reset()


def _is_number(tok):
    return bool(re.match(r'^\d', str(tok or '')))


def _is_op(tok):
    return bool(re.match(r'^[+\-*/%=<>!&|^~:.,()[\]{}]+$', str(tok or '')))


def _tone_for_name(name, previous_sig='', next_sig=''):
    """Return tone for a NAME token.

    - danger  -> Python keywords and builtins
    - success -> function/class names and callable names at call sites
    - text    -> ordinary variables, config items, constants, module names
    """
    text = str(name or '')
    previous_sig = str(previous_sig or '')
    next_sig = str(next_sig or '')

    if text in PY_KEYWORDS or text in PY_BUILTINS:
        return 'danger'

    if previous_sig in ('def', 'class'):
        return 'success'

    if next_sig == '(':
        return 'success'

    return 'text'


def _line_has_open_triple_string(line):
    """Return quote marker if line opens a triple string without closing it."""
    for marker in ('"""', "'''"):
        count = str(line or '').count(marker)
        if count % 2 == 1:
            return marker
    return ''


def _render_plain_line(line, state):
    """Render one code line with simple stateful Python highlighting."""
    text = str(line or '')
    i = 0
    previous_sig = state.get('previous_sig') or ''

    active_quote = state.get('triple_quote') or ''
    if active_quote:
        end = text.find(active_quote)
        if end < 0:
            # Docstrings/comments are softer than strings so large header
            # comments do not dominate the page.
            _write(text, 'muted')
            return

        _write(text[:end + 3], 'muted')
        state['triple_quote'] = ''
        i = end + 3

    while i < len(text):
        if text[i] == '#':
            _write(text[i:], 'muted')
            return

        if text.startswith('"""', i) or text.startswith("'''", i):
            marker = text[i:i + 3]
            end = text.find(marker, i + 3)

            if end < 0:
                _write(text[i:], 'muted')
                state['triple_quote'] = marker
                return

            _write(text[i:end + 3], 'muted')
            i = end + 3
            previous_sig = ''
            continue

        m = TOKEN_RE.match(text, i)
        if not m:
            _write(text[i], 'text')
            i += 1
            continue

        tok = m.group(0)

        if tok.startswith('"') or tok.startswith("'"):
            _write(tok, 'warning')
            previous_sig = ''
        elif _is_number(tok):
            _write(tok, 'warning')
            previous_sig = ''
        elif _is_op(tok):
            _write(tok, 'text')
        elif re.match(r'^[A-Za-z_]', tok):
            tone = _tone_for_name(tok, previous_sig=previous_sig)
            _write(tok, tone)

            if tok in ('def', 'class'):
                previous_sig = tok
            elif previous_sig in ('def', 'class'):
                previous_sig = ''
            elif tok not in PY_KEYWORDS:
                previous_sig = ''
        else:
            _write(tok, 'text')
            previous_sig = ''

        i = m.end()

    state['previous_sig'] = previous_sig


def _render_numbered_line(line, state, indent=''):
    """Render a PREVIEW-style line like ``0001: code``.

    Surface detail pages are user-facing, so we hide raw line numbers
    and render only the code/content portion. The source packet still
    keeps line numbers for exact reference when copied back.
    """
    prefix = str(indent or '')
    if prefix:
        _write(prefix, 'text')

    m = LINE_NO_RE.match(str(line or ''))
    if not m:
        _render_plain_line(line, state)
        print('')
        return

    _prefix, _number, rest = m.groups()

    if rest.startswith(' '):
        rest = rest[1:]

    _render_plain_line(rest, state)
    print('')


def render_code_lines(lines, max_lines=None, indent='   '):
    """Render syntax-highlighted code/output lines.

    Accepts either a string or an iterable of lines. PREVIEW-style line
    numbers are detected and hidden for readability.

    ``indent`` keeps code visually inside the page frame. Use ``''`` only
    for raw/full-width code output.
    """
    if isinstance(lines, str):
        rows = lines.splitlines()
    else:
        rows = list(lines or [])

    if max_lines is not None and len(rows) > max_lines:
        rows = rows[:max_lines] + ['... truncated: %d more line(s) ...' % (len(rows) - max_lines)]

    state = {
        'triple_quote': '',
        'previous_sig': '',
    }

    for line in rows:
        _render_numbered_line(line, state, indent=indent)
