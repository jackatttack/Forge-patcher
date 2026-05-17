# PIP

PIP installs or uninstalls pure-Python packages from PyPI into Pythonista's local site-packages folder.

It is intended for small packages that provide a `none-any` wheel.

## Syntax

Install:

    PIP install chardet

Directive form still works:

    PIP chardet
    ACTION: install

Install when package name differs from import name:

    PIP install beautifulsoup4
    IMPORT: bs4

Uninstall:

    PIP uninstall chardet
    CONFIRM: yes

## Directives

- ACTION: install | uninstall, optional when using inline syntax
- IMPORT: optional import module name when it differs from package name
- VERSION: currently reserved
- CONFIRM: required for uninstall

## Safety

PIP only supports pure-Python wheels.

Packages with compiled extensions, system binaries, Rust/C dependencies, or complex native builds will usually fail in Pythonista.

Install is verified by importing the package after extraction.

Uninstall uses the local `.pypi_packages` registry when available and falls back to removing a matching package folder or module file.

## Good workflow

    HELP PIP

    PIP chardet
    ACTION: install

    CREATE_FILE scratch/test_chardet.py
    BEGIN_BODY
    import chardet
    print("chardet ok")
    print(getattr(chardet, "__version__", "unknown"))
    END_BODY

    RUN_FILE scratch/test_chardet.py

Do not assume an install worked until the import check passes.