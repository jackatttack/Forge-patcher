help
====

HELP is the reboot self-description op.

Default HELP is rich and usage-first so an LLM can safely use the op without missing important syntax, examples, failures, or recovery notes.

    HELP SURFACE

Quick HELP is available when only a compact syntax reminder is wanted.

    HELP SURFACE quick

Full HELP is also accepted explicitly and currently matches the rich default.

    HELP SURFACE full
    HELP SURFACE --full
    HELP
    ARGS: SURFACE
    MODE: full

Contract HELP shows only package conformance/debug information.

    HELP SURFACE contract
    HELP SURFACE --contract
    HELP
    ARGS: SURFACE
    MODE: contract

Current sources:

    op.py SPEC
    op.py HELP
    manifest.py MANIFEST
    README.txt first useful content

Purpose:

    Forge explains itself to the user and the LLM.

Future scope:

    HELP package:<name>
    HELP file/path.py
    HELP docs/<slug>
