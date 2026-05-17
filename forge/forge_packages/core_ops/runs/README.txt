runs
====

RUNS exposes the reboot data layer.

It lists and inspects durable run artifacts written by forge_core.run_storage.

Examples:

    RUNS

    RUNS
    ARGS: latest

    RUNS
    ARGS: show 20260511_122038 packet

Purpose:

    structured runs should be inspectable without clipboard.

This is one of the big reboot differences from old Forge: behaviour can be tested and observed directly.
