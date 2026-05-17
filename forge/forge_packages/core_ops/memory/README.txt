# MEMORY

## Summary

MEMORY is the reboot public context and continuity op.

It is designed as a portable, non-personalised memory layer. In Jack's current environment it uses the historical `library/journal` backend so old Journal entries remain readable and writable without migration.

## Mental model

MEMORY means: retrieve or record durable context.

SEARCH finds source text. MEMORY finds lived/project context.

## Syntax

### Start context

    MEMORY start

### Recent entries by kind

    MEMORY code last 7

### All entries by kind

    MEMORY personal all

### Search memory

    MEMORY search forge docs

### Show one entry

    MEMORY show 20260424_084459_agxm

### Delete one entry

    MEMORY delete 20260424_084459_agxm
    CONFIRM: yes

### Add an entry

    MEMORY add code --tags forge progress
    BEGIN_BODY
    What changed and what should happen next.
    END_BODY

## Directives

- ARGS: command text, usually supplied same-line.
- TAGS: comma-separated tags for MEMORY add.
- LIMIT: cap list output.
- CONFIRM: yes — required for MEMORY delete.

## Compatibility

This first implementation intentionally uses `library/journal` as its backend.

That gives backwards compatibility with old Journal entries while allowing the public command to be MEMORY.

## Notes for LLMs

- Use MEMORY start at boot.
- Use MEMORY search <query> for targeted recall.
- Use MEMORY code last 7 for recent project continuity.
- Use MEMORY add code or MEMORY add personal for durable summaries/reflections.
- Do not read raw journal JSON unless debugging the memory backend.
