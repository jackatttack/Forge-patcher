audit
=====

AUDIT checks the reboot's own op package contract.

It should stay small and strict.

Current checks:

    op.py shape
    SPEC keys
    HELP summary
    validate/execute callability

Milestone 002 expands this to check:

    README.txt exists
    manifest.py exists
    MANIFEST keys exist
    MANIFEST op matches SPEC name
    MANIFEST name matches folder name

Purpose:

    Forge should be able to test and explain its own extension surface.
