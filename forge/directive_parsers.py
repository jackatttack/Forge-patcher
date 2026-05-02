# -*- coding: utf-8 -*-
"""
directive_parsers.py
====================
Helpers for strict directive parsing.
"""

def parse_key_value_line(line):
    """Parse 'KEY: value' directive line into (key, value) tuple or None."""
    s = (line or '').strip()
    if ':' not in s:
        return None, None
    key, value = s.split(':', 1)
    return key.strip(), value.strip()


def parse_lines_value(value):
    """Parse LINES: start-end directive value into (start, end) int tuple."""
    raw = (value or '').strip()
    if not raw:
        return None
    if '-' in raw:
        a, b = raw.split('-', 1)
        try:
            start = int(a.strip())
            end = int(b.strip())
            return (start, end)
        except Exception:
            return None
    try:
        n = int(raw)
        return (n, n)
    except Exception:
        return None
