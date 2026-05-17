PREVIEW is the reboot read-only source inspection op.

It intentionally follows current Forge PREVIEW syntax:

- PREVIEW path.py
- PREVIEW path.py
  LINES: 1-80
- PREVIEW path.py
  ANCHOR: def some_function
  CONTEXT: 6
- PREVIEW path.py::function
- PREVIEW path.py::Class.method

Do not use LIMIT. Reboot should avoid command-language drift from Forge2 unless a change is deliberate, documented, and worth the migration cost.
