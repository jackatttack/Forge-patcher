list_files
==========

LIST_FILES is the reboot orientation op.

It gives a compact project-relative directory view, while also returning structured data for Surface pages.

This reboot version now deliberately preserves important Forge2 LIST_FILES design ideas:

    README-aware directory summaries
    depth control
    optional file display
    optional docstring surfacing
    noisy directory exclusions
    structured metadata

Current directives:

    DEPTH
    FILES
    ALL
    DOCS
    README
    FILTER

Surface behaviour:

    LIST_FILES results generate files.tree.N pages.
    The main surface also shows a compact Files section.

Migration principle:

    Respect the mature Forge2 LIST_FILES behaviour.
    Do not reduce it to a dumb os.listdir wrapper.
