PACK
====

PACK creates a portable self-installing Python script from selected files.

It is useful for:

- exporting a clean Forge build
- creating local backups
- building an installer payload
- testing install shape on another Pythonista device

Output location
---------------

PACK writes into the Forge artifact area:

    forge/artifacts/packed/

Script mode writes:

    forge/artifacts/packed/<name>.py

Folder mode writes:

    forge/artifacts/packed/<name>/run_<name>.py
    forge/artifacts/packed/<name>/DO_NOT_OPEN_<name>_payload.py

Use folder mode for large packs so Pythonista opens the tiny launcher instead of the huge payload.

Syntax
------

    PACK my_pack
    DRY_RUN: yes
    EXCLUDE: artifacts/, scratch/, private/, token, secret
    BEGIN_BODY
    forge/README.txt
    forge/forge_core/
    END_BODY

Directives
----------

EXCLUDE

    Comma-separated path fragments to skip.

EXT

    Comma-separated file extensions, or * for all files.

DRY_RUN

    yes/no. Preview the report without writing output.

MODE

    script or folder. Default: script.

Safety
------

Generated installers install to the current working directory by default.

They also support:

    --help
    --list
    --dry-run
    --dry-run-here
    --dry-run-root PATH
    --install
    --install-here
    --install-root PATH

PACK warns about secret-looking paths but does not silently censor everything. Use EXCLUDE deliberately.