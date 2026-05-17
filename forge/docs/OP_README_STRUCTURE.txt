Forge Op README Structure
================================

Purpose
-------

Op READMEs should be surface-ready documents.

They are not just loose prose. They are durable teaching material for:
- Jack reading the system
- an LLM writing safe bundles
- HELP rendering rich usage context
- future LinkOS/Reboot surfaces rendering cards, syntax blocks, failure cards, and related-op chips

The README should be useful as plain text today and easy to render beautifully later.

Recommended structure
---------------------

# OP_NAME

## Summary

One or two sentences explaining what the op does.

## Mental model

Explain the op in the user language, not implementation language.

Example:
READ understands what exists.
INSERT adds without destroying.
REPLACE surgically changes what exists.

## Use when

Bullets describing good use cases.

## Do not use when

Bullets describing common wrong uses and the better op to use instead.

## Syntax

Use one subsection per supported shape.

### Shape name

    OP target
    DIRECTIVE: value
    BEGIN_BODY
    ...
    END_BODY

Syntax examples should be copyable and realistic.

## Directives

List each directive with a short explanation.

Example:
- LINES: start-end — explicit inclusive line range.
- OCCURRENCE: N — choose one repeated exact match.
- ALL: yes — apply to every exact match deliberately.

## Blocks

Only include this section when the op supports structured blocks such as BEGIN_BODY, BEGIN_OLD, BEGIN_NEW, BEGIN_EXPECT, etc.

## Examples

Use practical examples that show the intended workflow, not just isolated syntax.

Good examples often include:
1. READ/PREVIEW first
2. the mutating op
3. RUN/DIFF/REVERT follow-up if relevant

## Common failures

Use one subsection per failure.

### Failure message or status

Explain why it happens and what to do next.

## Safety and recovery

Explain touched files, DIFF, REVERT_RUN, branches, confirmations, and dangerous modes.

## Related ops

Use short descriptions.

Example:
- READ — inspect before editing.
- INSERT — add without replacing.
- REPLACE_FILE — overwrite a whole file deliberately.
- DIFF — review changes.
- REVERT_RUN — recover.

## Notes for LLMs

Operational instructions for AI agents.

This section should be blunt and practical:
- inspect first
- prefer safer syntax
- avoid broad edits
- run tests
- use HELP after parse failures
- avoid dangerous modes unless clearly intended

Rendering notes
---------------

Future surfaces should be able to map this structure into:
- summary hero
- use / do-not-use cards
- syntax cards
- directive tables
- block grammar panels
- common failure cards
- related-op chips
- LLM notes / safety footer

Do not rely on this being machine parsed perfectly yet. Keep the plain text readable first.
