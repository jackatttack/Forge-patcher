FORGE2
======

Purpose
-------
Forge is the next-generation Forge runtime and is the PRIMARY driver.
Forge 1 remains available as fallback only.

Runtime layout
--------------
- forge_entry.py     Shortcut entry point (PRIMARY)
- forge/entry.py        Local runtime entry helper
- forge/bridge.py       Parse -> execute -> packet -> run storage
- forge/parser_main.py  Strict bundle parser
- forge/engine.py       Execution engine
- forge/registry.py     Op registry + OP_SPECS (single source of truth)
- forge/validators.py   Op shape validation (imports OP_SPECS from registry)
- forge/run_packet.py   Packet formatter with run stamp
- forge/run_storage.py  Run persistence, revert, pruning (forge_runs/)
- forge/config.py       Constants: RUNS_DIRNAME, KEEP_RUNS
- forge/source_ops.py   Shared text/line helpers
- forge/ops/            One file per op

Adding an op
------------
1. Create forge/ops/my_op.py with SPEC, validate(), execute()
2. Add import + entry to OP_MODULES in registry.py
That is all. No other files need updating.

Working ops
-----------
File ops
- CREATE_FILE
- REPLACE_FILE
- REPLACE_FILE_RANGE
- REPLACE_FILE_LINES
- READ_FILE
- PREVIEW_FILE
- LIST_FILES
- COPY_FILE
- MOVE_FILE
- DELETE_FILE
- DELETE_DIR
- RUN_FILE
- GREP (exact, fuzzy, regex)
- HTTP_GET (planned)

Run management
- LIST_RUNS
- REVERT_RUN
- DIFF

Automation
- SHORTCUT (fires iOS Shortcut by name)

AST inspect
- PREVIEW
- LIST_TARGETS

AST write
- REPLACE
- REPLACE_LINES
- REPLACE_LINE
- INSERT_AFTER
- INSERT_BEFORE
- APPEND_INTO
- PREPEND_INTO
- INSERT_INTO

Planned
- REPLACE_INNER
- REPLACE_EXPR
- FIND_REPLACE
- HTTP_GET

Body syntax
-----------
All body-required ops use BEGIN_BODY / END_BODY:

    REPLACE file.py::Target
    BEGIN_BODY
    def target():
        return 123
    END_BODY

Key rules
---------
- forge_entry.py busts the forge module cache on every run
- New ops are picked up immediately without restarting Pythonista
- Run artifacts written to forge_runs/ after every successful execute
- REVERT_RUN restores file snapshots from a previous run
- DIFF shows changed lines between a run snapshot and current disk
- All file reads/writes use encoding='utf-8'
- op_specs.py has been deleted - OP_SPECS is derived from registry only
