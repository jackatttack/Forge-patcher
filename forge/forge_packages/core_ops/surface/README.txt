SURFACE
=======

SURFACE lets the assistant shape the user-facing view of a Forge run.

It does not edit files or perform domain work. It writes presentation intent into the structured run object so the renderer can choose a useful first view.

Mental model
------------

    packet = source of truth
    Surface = user-facing run view

The packet remains stable audit output. Surface makes the run easier to skim, navigate, and act on.

Use SURFACE when a bundle should return a clearer view of what matters.

Examples
--------

Focus on a file tree:

    SURFACE
    TITLE: Inspect project
    FOCUS: files.tree.0
    STACK: summary,files,ops,raw
    HERO: compact

    LIST_FILES .
    DEPTH: 2
    FILES: no

Focus on help:

    SURFACE
    TITLE: Learn REPLACE
    FOCUS: help.detail.0
    STACK: summary,help,raw
    HERO: compact

    HELP REPLACE

Fields
------

TITLE

    Optional title for the run surface.

FOCUS

    Page id to render first.

STACK

    Comma-separated page groups or page ids to expose.

HERO

    compact or full.

Why this exists
---------------

Without Surface, every run is just a packet.

That is reliable, but not always comfortable to use. Surface gives Forge a readable command view while keeping the packet as truth.