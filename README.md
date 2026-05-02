# Forge-patcher
Forge
=====

Forge is a clipboard-based patching and automation harness for Pythonista.

An AI model writes small text bundles called Forge bundles. You copy the bundle to the clipboard, run forge_entry.py, then Forge writes a run packet back to the clipboard. Paste that packet back to the AI so it can continue from real results.

Workflow
--------

1. AI writes a Forge bundle.
2. User copies the bundle to clipboard.
3. User runs forge_entry.py.
4. Forge executes the bundle against this folder.
5. Forge writes the run packet back to clipboard.
6. User pastes the packet back to the AI.
7. AI continues from the confirmed result.

Folder shape
------------

minimal_forge/
  forge_entry.py
  forge/
  artifacts/
  docs/

Core rule
---------

Inspect before editing.

Use LIST_FILES, PREVIEW, LIST_TARGETS, HELP, and BRANCH before making risky changes.

Good first command
------------------

LIST_OPS

