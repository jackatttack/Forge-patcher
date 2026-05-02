# -*- coding: utf-8 -*-
"""
ops.grep_ast
============
Search for a pattern across project files.

Directives:
    PATTERN     required - string to search for
    MATCH       exact|fuzzy|regex (default: exact)
    FILTER      optional - substring that must appear in relative file path
    LIMIT       optional - max number of hits to return (default: unlimited)
    EXT         optional - comma-separated file extensions (default: .py)

Target:
    - A file path to search one file
    - A directory path to search recursively under that directory
    - '.' to search recursively under the whole project root

Examples:
    EXT: .py
    EXT: .py,.md,.txt
"""

import os
import re

# Directories skipped during recursive file walks.
_SKIP_DIRS = {
    '.git',
    '.Trash',
    '__pycache__',
    'forge_runs',
    'site-packages',
    'site-packages-2',
    'site-packages-3',
    'stash',
    'stash_extensions',
    'patch_runs',
    'snapshots',
}

# Op identity, target kind, and directive contract.
SPEC = {
    'name': 'GREP',
    'target_kind': 'file',
    'body_mode': 'none',
    'allowed_directives': {'PATTERN', 'MATCH', 'FILTER', 'LIMIT', 'EXT', 'CONTEXT'},
    'required_directives': {'PATTERN'},
}

# Human-readable help shown by HELP GREP.
HELP = {
    'summary': 'Search across project files using exact, fuzzy, or regex matching. Supports optional context lines around hits.',
    'subject': ['Relative file path, directory path, or . for project-wide search.'],
    'common_failures': [
        'Missing PATTERN directive.',
        'MATCH must be exact, fuzzy, or regex.',
        'Invalid regex pattern.',
        'LIMIT must be an integer.',
        'CONTEXT must be an integer from 0 to 20.',
        'EXT must be a comma-separated list like .py,.md,.txt',
        'Target escapes project root.',
        'Missing or invalid target.',
    ],
    'safe_usage': [
        'Use exact mode first when you know the literal text.',
        'Use FILTER to narrow by relative path when project-wide search is too noisy.',
        'Use EXT to search docs as well as code, for example .py,.md,.txt.',
        'Use LIMIT to cap very large result sets.',
        'Use CONTEXT: 3 to show nearby lines around each hit.',
        'Use . for whole-project search, a directory for recursive subtree search, or a file for a single-file search.',
        'Default quick search: PATTERN only. This gives exact matching over .py files.',
        'Catch-up search: use MATCH: fuzzy with EXT: .py,.md,.txt and usually LIMIT: 20.',
        'Fuzzy mode is token-based and case-insensitive, so it works well for vague onboarding or project catch-up prompts.',
    ],
    'minimal_example': [
        'GREP .',
        'PATTERN: MEMORY_SYNC',
        '',
        'GREP',
        'PATTERN: def _side_drawer_begin',
        'FILTER: forge/forge_app/forge_run_centre.py',
        'CONTEXT: 5',
        '',
        'GREP .',
        'PATTERN: journal onboarding',
        'MATCH: fuzzy',
        'FILTER: journal/',
        'EXT: .py,.md,.txt',
        'LIMIT: 20',
    ],
    'related_ops': ['LIST_FILES', 'READ_FILE', 'PREVIEW'],
}

# Keyboard hint pills shown when GREP is typed.
HINTS = {
    '_max_hints': 1,
    'pattern': {
        'message': 'GREP needs PATTERN.',
        'why': 'Forge needs a search term before it can scan files.',
        'priority': 100,
        'example': [
            'GREP',
            'PATTERN: HINTS',
            'FILTER: forge/ops',
            'EXT: .py',
        ],
        'next': ['Add PATTERN: <text>', 'Use FILTER to narrow the search'],
    },
    'target': {
        'message': 'GREP target is optional, but FILTER is often clearer.',
        'why': 'Whole-project search works, but targeted searches are faster and easier to read.',
        'priority': 80,
        'example': [
            'GREP',
            'PATTERN: render_hints',
            'FILTER: forge',
            'EXT: .py',
        ],
        'next': ['Use FILTER: <folder> when searching a specific area'],
    },
    'match must be': {
        'message': 'GREP MATCH must be exact, fuzzy, or regex.',
        'why': 'Forge supports three search modes and rejects unknown values.',
        'priority': 120,
        'example': [
            'GREP',
            'PATTERN: render hints',
            'MATCH: fuzzy',
            'FILTER: forge',
            'EXT: .py',
        ],
        'next': ['Use MATCH: exact, MATCH: fuzzy, or MATCH: regex'],
    },
    'limit must be': {
        'message': 'GREP LIMIT must be a positive integer.',
        'why': 'Forge uses LIMIT to cap returned matches.',
        'priority': 120,
        'example': [
            'GREP',
            'PATTERN: HINTS',
            'FILTER: forge/ops',
            'EXT: .py',
            'LIMIT: 20',
        ],
        'next': ['Use LIMIT: 20 or omit LIMIT'],
    },
    'ext entries': {
        'message': 'GREP EXT entries must start with a dot.',
        'why': 'Forge expects extensions like .py, .md, or .txt.',
        'priority': 120,
        'example': [
            'GREP',
            'PATTERN: HINTS',
            'FILTER: forge/ops',
            'EXT: .py,.md,.txt',
        ],
        'next': ['Use EXT: .py or EXT: .py,.md,.txt'],
    },
    'ext cannot be empty': {
        'message': 'GREP EXT cannot be empty.',
        'why': 'Forge needs at least one file extension to search.',
        'priority': 120,
        'example': [
            'GREP',
            'PATTERN: HINTS',
            'EXT: .py',
        ],
        'next': ['Use EXT: .py or omit EXT for the default'],
    },
}


def validate(parsed_op):
    """Check PATTERN is present and MATCH/EXT/LIMIT/CONTEXT directives are valid."""
    errors = []
    if 'PATTERN' not in parsed_op.directives:
        errors.append('GREP requires PATTERN directive')

    match_mode = parsed_op.directives.get('MATCH', 'exact')
    if match_mode not in ('exact', 'fuzzy', 'regex'):
        errors.append('GREP MATCH must be exact, fuzzy, or regex, got: ' + str(match_mode))

    limit_raw = parsed_op.directives.get('LIMIT')
    if limit_raw not in (None, ''):
        try:
            limit = int(limit_raw)
            if limit < 1:
                errors.append('GREP LIMIT must be >= 1')
        except Exception:
            errors.append('GREP LIMIT must be an integer')

    context_raw = parsed_op.directives.get('CONTEXT')
    if context_raw not in (None, ''):
        try:
            context = int(context_raw)
            if context < 0:
                errors.append('GREP CONTEXT must be >= 0')
            elif context > 20:
                errors.append('GREP CONTEXT must be <= 20')
        except Exception:
            errors.append('GREP CONTEXT must be an integer')

    ext_raw = (parsed_op.directives.get('EXT') or '.py').strip()
    if not ext_raw:
        errors.append('GREP EXT cannot be empty')
    else:
        parts = [p.strip() for p in ext_raw.split(',') if p.strip()]
        if not parts:
            errors.append('GREP EXT cannot be empty')
        for part in parts:
            if not part.startswith('.'):
                errors.append('GREP EXT entries must start with "." e.g. .py,.md')

    return errors

def _normalize_ws(s):
    """Collapse all whitespace runs to single spaces and strip ends."""
    return ' '.join(s.split())


def _fuzzy_match(pattern, line):
    """Return True if all whitespace-normalised tokens in pattern appear in line."""
    needle = _normalize_ws(pattern).lower()
    hay = _normalize_ws(line).lower()
    if not needle:
        return False
    tokens = [t for t in needle.split(' ') if t]
    return all(tok in hay for tok in tokens)


def _parse_exts(ext_raw):
    """Parse comma-separated extension string into a tuple. Defaults to ('.py',)."""
    raw = (ext_raw or '.py').strip()
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    return tuple(parts or ['.py'])


def _collect_files(ctx, target_raw, exts):
    """Walk target path and return (file_list, error) filtered by extensions."""
    target_abs = os.path.realpath(os.path.join(ctx.project_root, target_raw))
    if not ctx.in_root(target_abs):
        return None, 'Target escapes project root'

    if os.path.isfile(target_abs):
        if target_abs.endswith(exts):
            return [target_abs], None
        return [], None

    if not os.path.isdir(target_abs):
        return None, 'File not found: ' + target_raw

    files = []
    for dirpath, dirnames, filenames in os.walk(target_abs):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(exts):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    return files, None


def execute(ctx, parsed_op, result):
    """Search files for pattern using exact, fuzzy, or regex match. Returns hits with optional context."""
    pattern     = parsed_op.directives.get('PATTERN', '')
    match_mode  = parsed_op.directives.get('MATCH', 'exact')
    path_filter = (parsed_op.directives.get('FILTER') or '').strip()
    limit_raw   = parsed_op.directives.get('LIMIT')
    limit       = None if limit_raw in (None, '') else int(limit_raw)
    context_raw = parsed_op.directives.get('CONTEXT')
    context     = 0 if context_raw in (None, '') else int(context_raw)
    context     = max(0, min(context, 20))
    exts        = _parse_exts(parsed_op.directives.get('EXT'))
    target_raw  = (parsed_op.target or '.').strip() or '.'

    if not pattern:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'GREP requires PATTERN'
        return

    files, err = _collect_files(ctx, target_raw, exts)
    if err:
        status = 'FAILED_INVALID_PATH' if 'escapes project root' in err else 'FAILED_IO'
        result['status'] = status
        result['message'] = err
        return

    regex_error = None
    scanned     = 0
    total_hits  = 0
    grouped_hits = {}

    for fpath in files:
        rel = os.path.relpath(fpath, ctx.project_root)

        if path_filter and path_filter not in rel:
            continue

        try:
            src = ctx.file_cache.get(fpath)
            if src is None:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    src = f.read()
        except Exception:
            continue

        scanned += 1
        lines = src.splitlines()

        for idx, line in enumerate(lines):
            lineno = idx + 1
            matched = False

            if match_mode == 'regex':
                try:
                    matched = re.search(pattern, line) is not None
                except re.error as e:
                    regex_error = str(e)
                    break
            elif match_mode == 'fuzzy':
                matched = _fuzzy_match(pattern, line)
            else:
                matched = pattern in line

            if matched:
                file_hits = grouped_hits.setdefault(rel, {})

                if context:
                    start = max(1, lineno - context)
                    end = min(len(lines), lineno + context)
                    for ctx_lineno in range(start, end + 1):
                        ctx_text = lines[ctx_lineno - 1].rstrip()
                        existing = file_hits.get(ctx_lineno)
                        is_match = ctx_lineno == lineno
                        if existing:
                            existing['match'] = existing.get('match', False) or is_match
                        else:
                            file_hits[ctx_lineno] = {'text': ctx_text, 'match': is_match}
                else:
                    file_hits[lineno] = {'text': line.rstrip(), 'match': True}

                total_hits += 1
                if limit is not None and total_hits >= limit:
                    break

        if regex_error:
            break
        if limit is not None and total_hits >= limit:
            break

    if regex_error:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'Invalid regex: ' + regex_error
        return

    files_hit = len(grouped_hits)

    header_lines = [
        "GREP %r [%d hits across %d files scanned, %d files hit]" % (
            pattern, total_hits, scanned, files_hit
        )
    ]
    if path_filter:
        header_lines.append("FILTER=%r" % path_filter)
    if exts:
        header_lines.append("EXT=%s" % ','.join(exts))
    if limit is not None:
        header_lines.append("LIMIT=%d" % limit)
    if context:
        header_lines.append("CONTEXT=%d" % context)

    out = ['\n'.join(header_lines)]

    if not grouped_hits:
        out.append('(no hits)')
    else:
        for rel in sorted(grouped_hits):
            out.append(rel)
            for lineno in sorted(grouped_hits[rel]):
                item = grouped_hits[rel][lineno]
                marker = '>' if item.get('match') else ' '
                out.append('  %s%04d: %s' % (marker, lineno, item.get('text', '')))

    result['status'] = 'APPLIED'
    result['message'] = '%d hits across %d files scanned' % (total_hits, scanned)
    result['preview'] = '\n'.join(out)
