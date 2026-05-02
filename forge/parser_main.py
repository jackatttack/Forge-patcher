# -*- coding: utf-8 -*-
"""
parser_main.py
==============
Forge bundle parser — converts raw bundle text into ParsedOp objects.

Handles op header detection, directive parsing, explicit BEGIN_BODY/END_BODY
delimiters, and implicit body collection. DEFAULT_FILE is threaded through
all ops in a bundle. Validates op shapes against SPEC after parsing.
"""

from forge.bundle_models import ParsedOp, ParseResult
from forge.directive_parsers import parse_key_value_line, parse_lines_value
from forge.lexer import is_exact_begin_body, is_exact_end_body
from forge.registry import OP_SPECS
from forge.validators import validate_op_shape


def _match_op_header(raw_line):
    """Match a line against known op names. Returns (op_name, target) or (None, None).

    Also matches PIXEL <OP> syntax for proxied pixel ops — returns ('PIXEL', 'OP target').
    """
    if raw_line and raw_line[0] in (' ', '\t'):
        return None, None
    s = (raw_line or '').strip()
    matches = []
    for op_name in OP_SPECS.keys():
        prefix = op_name + ' '
        if s == op_name or s.startswith(prefix):
            matches.append(op_name)
    if matches:
        matches.sort(key=len, reverse=True)
        op_name = matches[0]
        target = s[len(op_name):].strip()
        return op_name, target
    # PIXEL <OP> proxy syntax — PIXEL followed by any word
    if s.startswith('PIXEL '):
        rest = s[6:].strip()
        if rest:
            return 'PIXEL', rest
    return None, None

def parse_bundle(text):
    """
    Forge bundle parser.
    BEGIN_BODY / END_BODY are optional delimiters.
    Use them when body content contains lines that look like op headers.
    Without them, any non-directive content after directives is collected
    as the body until the next op header.
    """
    if not text or not text.strip():
        return ParseResult(ops=[], default_file=None, errors=[])

    lines = text.splitlines()
    ops = []
    errors = []
    default_file = None
    i = 0

    body_forbidden_ops = set(
        name for name, spec in OP_SPECS.items()
        if spec.get('body_mode') == 'forbidden'
    )

    def is_valid_directive_key(key):
        """Directive keys are ALL_CAPS with underscores only — no spaces."""
        return bool(key) and key == key.upper() and ' ' not in key

    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        raw = lines[i]
        s = raw.strip()

        if s.startswith('DEFAULT_FILE '):
            default_file = s[len('DEFAULT_FILE '):].strip() or None
            i += 1
            continue

        op_name, target = _match_op_header(raw)
        if not op_name:
            errors.append('Expected known op header at line %d: %r' % (i + 1, raw))
            return ParseResult(ops=ops, default_file=default_file, errors=errors)

        i += 1
        directives = {}
        body = ''

        while i < len(lines):
            line = lines[i]

            # Explicit body delimiter
            if is_exact_begin_body(line):
                i += 1
                body_lines = []
                while i < len(lines) and not is_exact_end_body(lines[i]):
                    body_lines.append(lines[i])
                    i += 1
                if i >= len(lines):
                    errors.append('Missing END_BODY for %s %s' % (op_name, target))
                    return ParseResult(ops=ops, default_file=default_file, errors=errors)
                i += 1
                body = '\n'.join(body_lines).rstrip() + '\n' if body_lines else ''
                break

            # Next op header — end of this op
            next_op_name, _ = _match_op_header(line)
            if next_op_name or line.strip().startswith('DEFAULT_FILE '):
                break

            if line.strip():
                key, value = parse_key_value_line(line)
                if key is not None and is_valid_directive_key(key):
                    # Valid directive
                    if key == 'LINES':
                        parsed = parse_lines_value(value)
                        if parsed is None:
                            errors.append('Invalid LINES directive at line %d: %r' % (i + 1, line))
                            return ParseResult(ops=ops, default_file=default_file, errors=errors)
                        directives[key] = parsed
                    elif key == 'LINE':
                        try:
                            directives[key] = int(value.strip())
                        except ValueError:
                            errors.append('Invalid LINE directive at line %d: %r' % (i + 1, line))
                            return ParseResult(ops=ops, default_file=default_file, errors=errors)
                    else:
                        directives[key] = value
                else:
                    # Not a directive — implicit body starts here
                    if op_name in body_forbidden_ops:
                        errors.append('Unexpected non-directive line at line %d: %r' % (i + 1, line))
                        return ParseResult(ops=ops, default_file=default_file, errors=errors)
                    body_lines = []
                    while i < len(lines):
                        next_op, _ = _match_op_header(lines[i])
                        if next_op or lines[i].strip().startswith('DEFAULT_FILE '):
                            break
                        body_lines.append(lines[i])
                        i += 1
                    body = '\n'.join(body_lines).rstrip() + '\n' if body_lines else ''
                    break

            i += 1

        # Inline args: for ops with target_kind == 'none', treat target text as ARGS.
        if target and op_name in OP_SPECS and OP_SPECS[op_name].get('target_kind') == 'none':
            if 'ARGS' not in directives:
                directives['ARGS'] = target
                target = ''
        ops.append(ParsedOp(
            op=op_name,
            target=target,
            directives=directives,
            body=body,
            default_file=default_file,
        ))

    final_errors = []
    for op in ops:
        final_errors.extend(validate_op_shape(op.op, op.directives, op.body))

    return ParseResult(ops=ops, default_file=default_file, errors=final_errors)


def main():
    """CLI entry point — reads bundle from stdin and prints the run packet."""
    demo = 'CREATE_FILE demo.txt\nBEGIN_BODY\nhello\nEND_BODY\n'
    result = parse_bundle(demo)
    print('ops =', len(result.ops))
    print('errors =', len(result.errors))


if __name__ == '__main__':
    main()
