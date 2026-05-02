# -*- coding: utf-8 -*-
"""
ops.replace_file_lines
======================
Anchor-based line range replacement in plain text files.

Directives:
    ANCHOR_START    required - substring to find start line
    ANCHOR_END      required - substring to find end line
    MATCH           exact|fuzzy (default: exact)
    OCCURRENCE      optional - 1-based ANCHOR_START match to use when repeated
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE_FILE_LINES',
    'target_kind': 'file',
    'body_mode': 'optional',

    'allowed_directives': {'ANCHOR_START', 'ANCHOR_END', 'MATCH', 'OCCURRENCE'},
    'required_directives': {'ANCHOR_START', 'ANCHOR_END'},
}

# HELP doc block — surfaces via HELP REPLACE_FILE_LINES.
HELP = {
    'summary': 'Replace a block in a plain text file using start and end anchors. Optional OCCURRENCE chooses the nth repeated start anchor.',
    'body': [
        'Wrap replacement lines in BEGIN_BODY / END_BODY.',
        'The body replaces everything from ANCHOR_START to ANCHOR_END inclusive.',
        'Use OCCURRENCE only after PREVIEW confirms which repeated anchor you intend to target.',
    ],
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'Missing ANCHOR_START or ANCHOR_END.',
        'Anchors match zero times or more than once.',
        'OCCURRENCE must be a positive integer if supplied.',
        'OCCURRENCE requested more matches than ANCHOR_START has.',
        'ANCHOR_END appears before ANCHOR_START.',
        'Omit body content (empty BEGIN_BODY / END_BODY) to delete the matched range.',
    ],
    'safe_usage': [
        'Use this when line numbers are unstable but text anchors are reliable.',
        'Pick unique anchors — PREVIEW first to confirm exact text.',
        'Prefer tighter anchors over OCCURRENCE when possible.',
        'Use OCCURRENCE for repeated structures only after visually confirming the candidate list.',
        'All three core parts are required: ANCHOR_START, ANCHOR_END, and BEGIN_BODY / END_BODY.',
    ],
    'minimal_example': [
        'REPLACE_FILE_LINES llm_workspace/memory.py',
        'ANCHOR_START: FLAGS = [',
        'ANCHOR_END: ]',
        'BEGIN_BODY',
        'FLAGS = [',
        "    'example flag',",
        ']',
        'END_BODY',
        '',
        'REPLACE_FILE_LINES docs/example.txt',
        'ANCHOR_START: ## Repeated section',
        'ANCHOR_END: ---',
        'OCCURRENCE: 2',
        'BEGIN_BODY',
        'replacement for the second repeated section',
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE_FILE', 'REPLACE_FILE_RANGE'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    '_max_hints': 1,
    'anchor_start': {
        'message': 'REPLACE_FILE_LINES needs ANCHOR_START.',
        'why': 'Forge needs a start anchor to find the first line of the replacement range in a flat file.',
        'priority': 100,
        'example': [
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: old first line',
            'ANCHOR_END: old last line',
            'BEGIN_BODY',
            'new first line',
            'new last line',
            'END_BODY',
        ],
        'next': ['PREVIEW the file and copy exact anchor text', 'HELP REPLACE_FILE_LINES'],
    },
    'anchor_end': {
        'message': 'REPLACE_FILE_LINES needs ANCHOR_END.',
        'why': 'Forge needs an end anchor to find the last line of the replacement range in a flat file.',
        'priority': 100,
        'example': [
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: old first line',
            'ANCHOR_END: old last line',
            'BEGIN_BODY',
            'new first line',
            'new last line',
            'END_BODY',
        ],
        'next': ['PREVIEW the file and copy exact anchor text', 'HELP REPLACE_FILE_LINES'],
    },
    'target': {
        'message': 'REPLACE_FILE_LINES needs a file path target.',
        'why': 'This op patches flat text files by path, not AST targets.',
        'priority': 90,
        'example': [
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: old first line',
            'ANCHOR_END: old last line',
            'BEGIN_BODY',
            'new line',
            'END_BODY',
        ],
        'next': ['LIST_FILES on the parent directory', 'HELP REPLACE_FILE_LINES'],
    },
    'file not found': {
        'message': 'File not found.',
        'why': 'REPLACE_FILE_LINES only patches existing files. Use CREATE_FILE if this should be a new file.',
        'priority': 130,
        'example': [
            'LIST_FILES docs',
            '',
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: old first line',
            'ANCHOR_END: old last line',
            'BEGIN_BODY',
            'new text',
            'END_BODY',
        ],
        'next': ['Check the path with LIST_FILES', 'Use CREATE_FILE for new files'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only patches files inside the Pythonista project root.',
        'priority': 130,
        'example': [
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: old first line',
            'ANCHOR_END: old last line',
            'BEGIN_BODY',
            'new text',
            'END_BODY',
        ],
        'next': ['Use a relative path under project root'],
    },
    'anchor_end appears before': {
        'message': 'ANCHOR_END was found before ANCHOR_START.',
        'why': 'The replacement range must move downward through the file.',
        'priority': 110,
        'example': [
            'PREVIEW docs/example.txt',
            '',
            'Then copy anchors in the same order they appear.',
        ],
        'next': ['PREVIEW the file', 'Swap or tighten anchors'],
    },
    'matched 0': {
        'message': 'Anchor text was not found in the file.',
        'why': 'The file may have drifted, whitespace differs, or the anchor was copied inaccurately.',
        'priority': 120,
        'example': [
            'PREVIEW docs/example.txt',
            '',
            'Then retry with anchors copied from the preview.',
        ],
        'next': ['PREVIEW the file', 'Try MATCH: fuzzy if whitespace differs'],
    },
    'matched 2': {
        'message': 'Anchor text matched more than once.',
        'why': 'Forge cannot safely choose which repeated range to patch.',
        'priority': 120,
        'example': [
            'REPLACE_FILE_LINES docs/example.txt',
            'ANCHOR_START: more distinctive start text',
            'ANCHOR_END: more distinctive end text',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ],
        'next': ['Use more specific anchors', 'Use a larger unique block of text'],
    },
    'skipped_anchor_mismatch': {
        'message': 'Anchor mismatch: patch against the live file text.',
        'why': 'The file content likely changed since the bundle was written.',
        'priority': 80,
        'example': [
            'PREVIEW docs/example.txt',
            '',
            'Then retry with anchors copied from the preview.',
        ],
        'next': ['PREVIEW the file', 'Tighten anchors or use REPLACE_FILE_RANGE'],
    },
}


def validate(parsed_op):
    """Check path, anchors, and optional OCCURRENCE are valid."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_FILE_LINES requires a target')
    if 'ANCHOR_START' not in parsed_op.directives:
        errors.append('REPLACE_FILE_LINES requires ANCHOR_START')
    if 'ANCHOR_END' not in parsed_op.directives:
        errors.append('REPLACE_FILE_LINES requires ANCHOR_END')

    occurrence_raw = (parsed_op.directives.get('OCCURRENCE') or '').strip()
    if occurrence_raw:
        try:
            occurrence = int(occurrence_raw)
            if occurrence < 1:
                errors.append('REPLACE_FILE_LINES OCCURRENCE must be >= 1')
        except Exception:
            errors.append('REPLACE_FILE_LINES OCCURRENCE must be a positive integer')

    return errors

def _normalize(s):
    """Collapse whitespace runs to single spaces for fuzzy anchor matching."""
    return ' '.join((s or '').strip().split())


def _find_anchor(lines, anchor, match_mode, target_path=None):
    """Find matching line indexes and return rich diagnostic text for failures."""
    needle = anchor or ''
    hits = []
    for idx, line in enumerate(lines):
        if match_mode == 'fuzzy':
            if _normalize(needle) in _normalize(line):
                hits.append(idx)
        else:
            if needle in line:
                hits.append(idx)

    def _line_preview(i):
        text = (lines[i] or '').strip()
        if len(text) > 80:
            text = text[:77] + '...'
        return "  line %d: %s" % (i + 1, text)

    def _preview_block(i):
        if not target_path:
            return ''
        start = max(1, i + 1 - 6)
        end = min(len(lines), i + 1 + 6)
        return '\n'.join([
            '  PREVIEW %s' % target_path,
            '  LINES: %d-%d' % (start, end),
        ])

    detail = ''
    if len(hits) == 0:
        detail = 'Anchor matched 0 times, expected 1'

        # Best-effort fuzzy suggestions when exact matching found nothing.
        suggestions = []
        norm_needle = _normalize(needle).lower()
        if norm_needle:
            needle_words = [w for w in norm_needle.split() if len(w) > 2]
            for idx, line in enumerate(lines):
                norm_line = _normalize(line).lower()
                if not norm_line:
                    continue
                if norm_needle in norm_line or any(w in norm_line for w in needle_words):
                    suggestions.append(idx)
                if len(suggestions) >= 5:
                    break

        if suggestions:
            detail += '\nNear matches:\n' + '\n'.join(_line_preview(i) for i in suggestions)
            if target_path:
                detail += '\nSuggested previews:\n'
                detail += '\n\n'.join(_preview_block(i) for i in suggestions[:3])

    elif len(hits) != 1:
        detail = 'Anchor matched %d times, expected 1' % len(hits)
        detail += '\nCandidates:\n' + '\n'.join(_line_preview(i) for i in hits[:8])
        if len(hits) > 8:
            detail += '\n  ... %d more' % (len(hits) - 8)
        if target_path:
            detail += '\nSuggested previews:\n'
            detail += '\n\n'.join(_preview_block(i) for i in hits[:4])

    return hits, detail

def execute(ctx, parsed_op, result):
    """Resolve path, find anchor range, replace matched lines with body content."""
    target_raw = (parsed_op.target or '').strip()
    file_abs = os.path.realpath(os.path.join(ctx.project_root, target_raw))

    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + target_raw
        return

    src = ctx.file_cache.get(file_abs)
    if src is None:
        with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
            src = f.read()

    match_mode = parsed_op.directives.get('MATCH', 'exact')
    anchor_start = parsed_op.directives.get('ANCHOR_START', '')
    anchor_end = parsed_op.directives.get('ANCHOR_END', '')

    occurrence_raw = (parsed_op.directives.get('OCCURRENCE') or '').strip()
    occurrence = None
    if occurrence_raw:
        try:
            occurrence = int(occurrence_raw)
        except Exception:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'OCCURRENCE must be a positive integer'
            return
        if occurrence < 1:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'OCCURRENCE must be >= 1'
            return

    lines = src.splitlines()

    hits_s, detail_s = _find_anchor(lines, anchor_start, match_mode, target_raw)
    hits_e, detail_e = _find_anchor(lines, anchor_end, match_mode, target_raw)

    occurrence_note = ''

    if occurrence is not None:
        if not hits_s:
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = 'ANCHOR_START %r matched 0 times; OCCURRENCE %d cannot be used' % (
                anchor_start, occurrence
            )
            if detail_s:
                result['message'] += '\n' + detail_s
            return

        if occurrence > len(hits_s):
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = (
                'ANCHOR_START %r matched %d times; OCCURRENCE %d is out of range'
                % (anchor_start, len(hits_s), occurrence)
            )
            if detail_s:
                result['message'] += '\n' + detail_s
            return

        line_s = hits_s[occurrence - 1]
        end_candidates = [i for i in hits_e if i >= line_s]
        if not end_candidates:
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = (
                'OCCURRENCE %d selected ANCHOR_START at line %d, but no ANCHOR_END was found after it'
                % (occurrence, line_s + 1)
            )
            if detail_e:
                result['message'] += '\n' + detail_e
            return

        line_e = end_candidates[0]
        occurrence_note = (
            ' using OCCURRENCE %d of %d at line %d; ANCHOR_END resolved at line %d'
            % (occurrence, len(hits_s), line_s + 1, line_e + 1)
        )

    else:
        if len(hits_s) != 1:
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = 'ANCHOR_START %r matched %d times, expected 1' % (anchor_start, len(hits_s))
            if detail_s:
                result['message'] += '\n' + detail_s
            return
        if len(hits_e) != 1:
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = 'ANCHOR_END %r matched %d times, expected 1' % (anchor_end, len(hits_e))
            if detail_e:
                result['message'] += '\n' + detail_e
            return

        line_s = hits_s[0]
        line_e = hits_e[0]

    if line_e < line_s:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'ANCHOR_END appears before ANCHOR_START'
        return

    replacement = (parsed_op.body or '').splitlines()
    new_lines = lines[:line_s] + replacement + lines[line_e + 1:]
    patched = '\n'.join(new_lines)
    if src.endswith('\n'):
        patched += '\n'

    if patched == src:
        result['status'] = 'SKIPPED_ALREADY_APPLIED'
        result['message'] = 'No change'
        return

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(patched)

    ctx.file_cache[file_abs] = patched
    ctx.touched_files[file_abs] = {'before': src, 'after': patched}

    result['file'] = os.path.relpath(file_abs, ctx.project_root)
    result['status'] = 'APPLIED'
    result['message'] = 'Lines %d-%d replaced%s' % (line_s + 1, line_e + 1, occurrence_note)
