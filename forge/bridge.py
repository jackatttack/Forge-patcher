# -*- coding: utf-8 -*-
"""
forge.bridge
=============
Thin wrappers over forge local core.
"""

from forge.parser_main import parse_bundle
from forge.engine import execute_ops
from forge.run_packet import format_run_packet


def _hints_for_error(err):
    """Render parse-time hints for an error string when possible."""
    from forge.registry import get_op_module, OP_SPECS
    from forge.hinting import render_hints_for_errors

    op_found = None

    # Prefer structured validator diagnostics, e.g.:
    # OP: INSERT_AFTER
    # This avoids fuzzy substring detection grabbing a different op mentioned
    # inside compatibility hints.
    try:
        import re
        match = re.search(r'(?m)^OP:\s*([A-Z_][A-Z0-9_]*)\s*$', err)
        if match:
            candidate = match.group(1)
            if candidate in OP_SPECS:
                op_found = candidate
    except Exception:
        op_found = None

    # Fallback for older/simple errors that only contain the op name inline.
    if op_found is None:
        for op_name in sorted(OP_SPECS.keys(), key=len, reverse=True):
            if op_name in err:
                op_found = op_name
                break

    if op_found is None:

        if 'Expected known op header' in err:
            bad_line = ''
            line_no = ''
            try:
                import re
                line_match = re.search(r'line\s+(\d+)', err)
                if line_match:
                    line_no = line_match.group(1)
                match = re.search(r": '([^']*)'", err)
                if match:
                    bad_line = match.group(1)
            except Exception:
                bad_line = ''

            stripped = (bad_line or '').strip()
            first_word = stripped.split(None, 1)[0] if stripped else ''
            known_ops = set(OP_SPECS.keys())

            lines = [
                'HINT: Forge could not parse this bundle.',
            ]
            if line_no:
                lines.append('LINE: ' + line_no)
            if bad_line:
                lines.append('TEXT: ' + bad_line)

            # REPLACE_BLOCK marker leakage / marker used outside body.
            if stripped in ('BEGIN_OLD', 'END_OLD', 'BEGIN_NEW', 'END_NEW'):
                lines.extend([
                    'WHY: %s is not a top-level Forge op header.' % stripped,
                    'REPLACE_BLOCK markers only work inside that op body.',
                    'EXAMPLE:',
                    'REPLACE_BLOCK docs/example.txt',
                    'BEGIN_BODY',
                    'BEGIN_OLD',
                    'old text',
                    'END_OLD',
                    'BEGIN_NEW',
                    'new text',
                    'END_NEW',
                    'END_BODY',
                    'NEXT:',
                    '- Put BEGIN_OLD / BEGIN_NEW markers inside REPLACE_BLOCK.',
                    '- Do not use them as top-level bundle lines.',
                ])
                return '\n'.join(lines)

            # Directive-shaped line without an active op.
            if ':' in stripped:
                key = stripped.split(':', 1)[0].strip()
                if key and key == key.upper() and ' ' not in key:
                    lines.extend([
                        'WHY: This looks like a directive, but Forge was expecting an op header here.',
                        'DIRECTIVE WITHOUT OP: ' + key,
                        'EXAMPLE:',
                        'RUN_FILE path/to/file.py',
                        'ARGS: optional args here',
                        'NEXT:',
                        '- Put directives immediately under a valid op header.',
                        '- Or put plain text inside BEGIN_BODY / END_BODY for an op that accepts a body.',
                    ])
                    return '\n'.join(lines)

            upperish = bool(first_word) and first_word == first_word.upper() and any(
                c.isalpha() for c in first_word
            )

            # Looks like an unregistered op.
            if upperish and first_word not in known_ops:
                lines.extend([
                    'WHY: This looks like an op header, but it is not registered in Forge right now.',
                    'UNKNOWN OP: ' + first_word,
                ])

                if first_word.startswith('REPLACE_') or first_word.startswith('INSERT_') or first_word.endswith('_BLOCK'):
                    lines.extend([
                        'POSSIBLE CAUSE:',
                        '- The op name may be mistyped.',
                        '- Or the bundle may be trying to use a newly-created op in the same run that creates it.',
                        'IMPORTANT:',
                        '- Forge parses the whole bundle before execution.',
                        '- A new op must be installed/refreshed in one bundle, then used in a second bundle.',
                    ])

                lines.extend([
                    'EXAMPLE:',
                    'LIST_OPS all',
                    '',
                    'HELP <known-op-name>',
                    'NEXT:',
                    '- Run LIST_OPS all to check the registered op names.',
                    '- If you just created this op, run REFRESH first, then use it in a new bundle.',
                ])
                return '\n'.join(lines)

            # Planning/comment text.
            if stripped.startswith('#') or stripped.startswith('- ') or stripped.startswith('* '):
                lines.extend([
                    'WHY: Runnable bundles cannot contain planning notes or comments at top level.',
                    'EXAMPLE:',
                    'Do not put comments in the runnable bundle:',
                    'BRANCH create before_change',
                    'BEGIN_BODY',
                    'forge/file.py',
                    'END_BODY',
                    'NEXT:',
                    '- Keep planning text outside the runnable bundle.',
                    '- Or put it inside BEGIN_BODY / END_BODY if you are writing it to a file or journal entry.',
                ])
                return '\n'.join(lines)

            # Generic fallback.
            lines.extend([
                'WHY: Runnable bundles can only contain op headers, directives, and body content inside BEGIN_BODY / END_BODY.',
                'EXAMPLE:',
                'Use a known op header such as:',
                'HELP BRANCH',
                '',
                'or put plain text inside an op body:',
                'CREATE_FILE scratch/note.txt',
                'BEGIN_BODY',
                'plain text here',
                'END_BODY',
                'NEXT:',
                '- Run LIST_OPS all if the op name is unknown.',
                '- Keep design notes outside the runnable bundle unless they are inside BEGIN_BODY / END_BODY.',
            ])
            return '\n'.join(lines)

        return ''

    mod = get_op_module(op_found)
    if mod is None:
        return ''

    hint_block = render_hints_for_errors(mod, [err])
    lines = []
    if hint_block:
        lines.append(hint_block)

    help_line = 'HELP ' + op_found
    if help_line not in hint_block:
        lines.append('See: ' + help_line)

    return '\n'.join(lines)

def run_bundle(bundle_text, project_root, step=None, max_steps=None):
    from forge.run_storage import write_run_artifacts, prune_runs, now_stamp

    try:
        from forge.alias_expander import try_expand_alias
        expanded = try_expand_alias(bundle_text, project_root)
    except Exception:
        expanded = None

    if expanded is not None:
        bundle_text = expanded

    normalise_notes = []
    try:
        from forge.compat_normalizer import normalise_bundle
        bundle_text, normalise_notes = normalise_bundle(bundle_text)
    except Exception:
        normalise_notes = []

    parsed = parse_bundle(bundle_text)
    synthetic_results = []

    if parsed.errors:
        for err in parsed.errors:
            msg = err
            hint_block = _hints_for_error(err)
            if hint_block:
                msg += '\n' + hint_block
            synthetic_results.append({
                'op': 'PARSE',
                'target': '<bundle>',
                'status': 'FAILED_PARSE',
                'message': msg,
                'preview': '',
            })

    elif bundle_text and bundle_text.strip() and not parsed.ops:
        synthetic_results.append({
            'op': 'PARSE',
            'target': '<bundle>',
            'status': 'FAILED_PARSE',
            'message': 'No ops parsed from non-empty bundle',
            'preview': bundle_text[:800],
        })

    if synthetic_results:
        try:
            from forge.compat_events import record_run
            record_run(
                project_root,
                stamp='',
                results=synthetic_results,
                normalise_notes=normalise_notes,
                source='parse',
            )
        except Exception:
            pass

        packet = format_run_packet(
            synthetic_results,
            step=step,
            max_steps=max_steps,
            normalise_notes=normalise_notes,
        )
        return {
            'parsed': parsed,
            'context': None,
            'packet': packet,
        }

    stamp = now_stamp()
    ctx = execute_ops(parsed.ops, project_root, default_file=parsed.default_file)

    try:
        write_run_artifacts(project_root, stamp, bundle_text, ctx.results, ctx.touched_files)
        prune_runs(project_root)
    except Exception:
        pass

    try:
        from forge.compat_events import record_run
        record_run(
            project_root,
            stamp=stamp,
            results=ctx.results,
            normalise_notes=normalise_notes,
            source='run',
        )
    except Exception:
        pass

    packet = format_run_packet(
        ctx.results,
        stamp=stamp,
        step=step,
        max_steps=max_steps,
        normalise_notes=normalise_notes,
    )
    return {
        'parsed': parsed,
        'context': ctx,
        'packet': packet or None,
        'stamp': stamp,
    }
