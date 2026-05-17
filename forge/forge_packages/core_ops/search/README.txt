# SEARCH

## Summary

SEARCH is the reboot text search op.

Use it for orientation before reading or editing.

## Mental model

SEARCH finds candidate locations. READ inspects the exact thing.

## Syntax

Explicit bundle shape:

    SEARCH forge
    QUERY: package contract

Path-first shortcut:

    SEARCH forge FOR package contract

Query-first shortcut:

    SEARCH package contract IN forge

Single-file search:

    SEARCH forge/smoke.py FOR main

Filtered search:

    SEARCH forge FOR surface
    EXT: .py,.txt
    LIMIT: 40

## Directives

- QUERY: text — explicit search text.
- EXT: .py,.txt — restrict file extensions.
- LIMIT: N — cap matches. Default: 80.
- CASE: yes — use case-sensitive matching.

## Notes for LLMs

- Prefer SEARCH path FOR text for simple searches.
- Use QUERY when the search text is long, awkward, or contains words like IN/FOR.
- After SEARCH finds candidates, use READ on the specific file or AST target.
- SEARCH is read-only. It should not touch files or create snapshots.
