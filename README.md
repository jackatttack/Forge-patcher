#forge patcher
Forge is a clipboard-based patching and automation harness for Pythonista on iOS.
An AI model writes small plain-text instructions called **Forge bundles**. You copy a bundle to the clipboard, run `forge_entry.py`, and Forge executes it locally. Forge then writes a **run packet** back to the clipboard. Paste that packet back to the AI so it can continue from real results.
The run packet is the source of truth.
## What Forge is for
Forge gives an AI a controlled way to:
- inspect files
- create files
- patch code
- move or delete files
- run Python scripts
- create restore branches
- recover from bad edits
It is not background automation. It is a tight human-in-the-loop loop:
```text
AI writes bundle -> you run Forge -> Forge returns packet -> AI continues

Folder shape

forge_entry.py
forge/
  ops/
  guides/
  artifacts/
docs/

First setup

1. Put this repository somewhere Pythonista can run it.
2. Open forge_entry.py once in Pythonista.
3. Create an iOS Shortcut that runs forge_entry.py.
4. Optional but recommended: put that Shortcut on your Home Screen or Action Button.

You can run forge_entry.py manually, but a Shortcut makes the loop much faster.

First AI boot

Open:

docs/AI_FIRST_BOOT.txt

Copy its contents into your AI chat.

Then open:

docs/MINIMAL_BOOT_BUNDLE.txt

Copy that bundle to your clipboard and run forge_entry.py.

Forge will replace your clipboard with a run packet. Paste that packet back to the AI.

Learning Forge

Forge includes built-in workflow guides. The AI can read them through the GUIDE op.

Useful first guides:

GUIDE
ARGS: first-boot
GUIDE
ARGS: tutorial
GUIDE
ARGS: inspect-first
GUIDE
ARGS: safe-patch
GUIDE
ARGS: custom-ops

Use HELP for exact op syntax:

HELP CREATE_FILE

Use GUIDE for workflow advice:

GUIDE
ARGS: tutorial

Good first bundle

LIST_FILES .
DEPTH: 2
FILES: yes
LIST_OPS
GUIDE
ARGS: list
GUIDE
ARGS: first-boot
GUIDE
ARGS: tutorial
HELP GUIDE
HELP LIST_FILES
HELP CREATE_FILE
HELP RUN_FILE

Core rule

Inspect before editing.

Start with LIST_FILES, PREVIEW, GREP, LIST_TARGETS, HELP, and GUIDE. Use BRANCH before risky changes.

Small bundles are better than huge ones.