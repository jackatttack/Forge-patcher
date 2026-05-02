# -*- coding: utf-8 -*-
"""
engine.py
=========
Forge execution engine — runs parsed ops in sequence against a shared context.

Handles $OUT substitution between ops, validate/execute dispatch, hint
injection on failures, and ctx.last update after each op. Returns an
EngineContext containing all results.
"""

from forge.engine_context import EngineContext
from forge.registry import get_op_module
from forge.result_models import make_result


def execute_ops(parsed_ops, project_root, default_file=None):
    """Run a list of ParsedOp objects in sequence, returning the final EngineContext."""
    ctx = EngineContext(project_root, default_file=default_file)

    for op in parsed_ops:
        # Substitute $OUT.field and $LAST_OUTPUT in directives and target
        if ctx.last or ctx.last_output:
            def _sub(text):
                if not isinstance(text, str):
                    return text
                # $OUT.lines.N
                import re
                def _lines_sub(m):
                    try:
                        idx = int(m.group(1))
                        lines = ctx.last.get('lines') or []
                        return lines[idx] if -len(lines) <= idx < len(lines) else ''
                    except Exception:
                        return ''
                text = re.sub(r'\$OUT\.lines\.([-\d]+)', _lines_sub, text)
                # $OUT.field
                def _field_sub(m):
                    return str(ctx.last.get(m.group(1), ''))
                text = re.sub(r'\$OUT\.([a-zA-Z_][a-zA-Z0-9_]*)', _field_sub, text)
                # $LAST_OUTPUT backwards compat
                text = text.replace('$LAST_OUTPUT', ctx.last_output)
                return text

            op.target = _sub(op.target or '')
            op.directives = {k: _sub(v) for k, v in op.directives.items()}

        result = make_result(op.op, op.target)
        mod = get_op_module(op.op)

        if mod is None:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'Unknown op: ' + str(op.op)
            ctx.results.append(result)
            continue

        # Safety guard: mutating edits to Forge core require explicit confirmation.
        #
        # Important fail-safe:
        # If core_guard.py itself is broken, read-only ops should still run so Forge
        # remains inspectable/recoverable. Mutating ops are blocked until the guard is fixed.
        try:
            from forge.core_guard import needs_confirm, has_confirm, guard_message
            if needs_confirm(op) and not has_confirm(op):
                result['status'] = 'FAILED_CORE_GUARD'
                result['message'] = guard_message(op)
                ctx.results.append(result)
                continue
        except Exception as e:
            mutating_prefixes = (
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
            op_name = (op.op or '').upper()
            is_mutating = op_name.startswith(mutating_prefixes)

            if is_mutating:
                result['status'] = 'FAILED_CORE_GUARD'
                result['message'] = (
                    'Core guard unavailable: %s: %s\n'
                    'WHY: Forge could not safely verify whether this mutating op touches protected core files.\n'
                    'READ-ONLY OPS STILL WORK: use HELP, PREVIEW, READ_FILE, LIST_FILES, or LIST_TARGETS to inspect and repair.\n'
                    'NEXT:\n'
                    '- Restore a recent branch if the guard was just edited.\n'
                    '- Or inspect forge/core_guard.py and fix the syntax/import error.\n'
                    '- Do not run mutating ops until the guard imports cleanly.'
                ) % (type(e).__name__, e)
                ctx.results.append(result)
                continue

            # Non-mutating/read-only ops are allowed to continue if the guard is broken.
            pass

        validate = getattr(mod, 'validate', None)
        if validate is not None:
            errors = validate(op)
            if errors:
                result['status'] = 'FAILED_PARSE'
                msg = '; '.join(errors)
                hint_block = _get_hints(mod, errors)
                if hint_block:
                    msg += '\n' + hint_block
                msg += '\nSee: HELP ' + str(op.op)
                result['message'] = msg
                ctx.results.append(result)
                continue

        execute = getattr(mod, 'execute', None)
        if execute is None:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'No execute() for op: ' + str(op.op)
            ctx.results.append(result)
            continue

        try:
            execute(ctx, op, result)
        except Exception as e:
            result['status'] = 'FAILED_PARSE'
            msg = type(e).__name__ + ': ' + str(e)
            hint_block = _get_hints(mod, [msg])
            if hint_block:
                msg += '\n' + hint_block
            msg += '\nSee: HELP ' + str(op.op)
            result['message'] = msg

        # Surface hints for runtime failures.
        # If an op already emitted rich diagnostics, do not add generic hints below it.
        status = result.get('status', '')
        if status not in ('APPLIED', 'SKIPPED_ALREADY_APPLIED', 'SKIPPED_ALREADY_PRESENT'):
            msg = result.get('message', '')
            rich_markers = (
                'Candidates:',
                'Near matches:',
                'Suggested preview:',
                'Suggested previews:',
                'Core Forge file edit blocked:',
                'Core guard unavailable:',
            )
            if msg and not any(marker in msg for marker in rich_markers):
                hint_block = _get_hints(mod, [status + ' ' + msg])
                if hint_block:
                    result['message'] = msg + '\n' + hint_block

        # Update ctx.last and ctx.last_output from result
        out = result.get('out')
        if out:
            ctx.last = out
            ctx.last_output = str(out.get('stdout', ''))
        else:
            stdout = result.get('stdout')
            if stdout is not None:
                ctx.last_output = stdout
                ctx.last = {
                    'stdout': stdout,
                    'lines': [l for l in stdout.splitlines() if l.strip()],
                }
            else:
                preview = result.get('preview') or ''
                if preview:
                    ctx.last_output = preview.strip()
                    ctx.last = {
                        'stdout': preview.strip(),
                        'lines': [l for l in preview.strip().splitlines() if l.strip()],
                    }

        ctx.results.append(result)

    return ctx

def _get_hints(mod, errors):
    """Match error strings against op HINTS and return formatted hint blocks."""
    from forge.hinting import render_hints_for_errors
    return render_hints_for_errors(mod, errors)
