Forge
=====

Purpose
-------

Forge is a clipboard-driven development harness for Pythonista on iOS.

It lets an AI assistant write small, inspectable command bundles. The user runs those bundles locally, Forge applies the requested operations, stores recovery data, and returns a run packet. That packet is the source of truth for the next step.

Forge is designed for a tight development loop:

    AI writes bundle
        -> user runs it locally
        -> Forge parses and executes
        -> Forge stores the run
        -> packet returns to chat
        -> AI inspects the packet before continuing

Core ideas
----------

1. The packet is truth.
2. The user stays in control.
3. Every write should be inspectable and recoverable.
4. Small bundles beat clever bundles.
5. Surface pages make runs easier to skim, navigate, and act on.
6. Ops should explain themselves through HELP and focused docs.
7. Public commands should stay boring, stable, and easy to copy.

Main public verbs
-----------------

Inspection:

    LIST_FILES
    READ
    SEARCH
    LIST_TARGETS
    HELP
    LIST_OPS

Editing:

    CREATE_FILE
    REPLACE_FILE
    REPLACE
    INSERT
    DELETE
    MOVE
    COPY

Validation and recovery:

    RUN_FILE
    AUDIT
    DIFF
    RUNS
    REVERT_RUN
    BRANCH

Presentation:

    SURFACE

The loop
--------

Nothing changes until the user runs a bundle locally.

The assistant should never claim that a file changed unless a run packet confirms it. A failed packet is useful: read the status, hints, touched files, and preview before deciding the next move.

Safe working pattern
--------------------

Before editing:

    SEARCH for the area
    READ the target
    READ with TARGETS: yes for Python structure
    HELP the op if syntax is not fresh

Then patch with the smallest write mode that fits:

    REPLACE for existing code or text
    INSERT for new code beside or inside a target
    CREATE_FILE for new files
    REPLACE_FILE only when a full rewrite is clearer than many small patches

After editing:

    DIFF current
    AUDIT
    RUN_FILE relevant_test.py

Surface
-------

Surface is the user-facing view of a run.

The packet remains the audit trail. Surface makes the run easier to use: summaries, focused pages, controls, navigation, and copyable actions. A good Surface page should answer:

    What happened?
    What matters?
    What can I do next?

Getting started
---------------

For a first safe orientation run:

    LIST_FILES .
    DEPTH: 2
    FILES: no

    LIST_OPS

This changes no project files. It gives the assistant a project map and the current command vocabulary.

AI boot docs
------------

Forge includes two AI boot prompts at the top level.

For a new user who wants the assistant to teach Forge step by step:

    AI_FIRST_BOOT.txt

For an experienced user who wants the shortest useful working prompt:

    AI_MINIMAL_BOOT.txt

Copy one of those into a fresh AI chat, then follow the returned bundle.
