# DELETE

## Summary

DELETE is the reboot public deletion op.

It deletes whole files, explicit file line ranges, or exact old text blocks while recording recovery metadata for DIFF and REVERT_RUN.

## Mental model

DELETE means: remove something that already exists.

It is the destructive sibling of REPLACE. REPLACE changes existing content; DELETE removes existing content.

## Use when

- You want to remove a file.
- You want to remove a known line range.
- You want to remove an exact text block.
- You want deletion to be tracked for DIFF and REVERT_RUN.

## Do not use when

- You want to change text rather than remove it. Use REPLACE.
- You want to add text. Use INSERT.
- You have not inspected the target. Use READ first.
- You want AST deletion. Not supported yet.

## Syntax

    DELETE scratch/example.txt
    CONFIRM: yes

    DELETE docs/example.txt
    LINES: 12-15
    CONFIRM: yes

    DELETE docs/example.txt
    CONFIRM: yes
    BEGIN_OLD
    exact text to remove
    END_OLD

## Directives

- CONFIRM: yes — required for all DELETE modes.
- LINES: start-end — delete an explicit inclusive file line range.
- OCCURRENCE: N — in exact block mode, delete the Nth matching OLD block.
- ALL: yes — in exact block mode, delete every matching OLD block.

## Notes for LLMs

- Always READ before range or block deletion unless the user gave exact current text.
- Do not use DELETE for AST targets yet.
- Prefer DELETE + LINES for small inspected slices.
- Prefer DELETE + BEGIN_OLD for exact copied blocks when line numbers are awkward.
- Never use ALL: yes casually.
- Always include CONFIRM: yes.
