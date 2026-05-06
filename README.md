# Forge

Forge is a clipboard-based patching and automation harness for Pythonista on iOS.

You work with an AI assistant. The assistant writes a plain-text Forge bundle. You copy that bundle to your clipboard, run forge_entry.py in Pythonista, and Forge executes the bundle locally. Forge then writes a run packet back to your clipboard. You paste that packet back to the assistant.

The run packet is the source of truth. The assistant should not claim a file changed, moved, deleted, uploaded, or tested unless the packet confirms it.

## The loop

AI writes bundle -> you run Forge -> Forge returns packet -> AI continues

Forge gives an AI a safe local command surface:

- inspect files
- preview code and text
- search the project
- patch files
- run Python files
- create, move, copy, and delete files
- checkpoint before risky edits
- recover from bad runs
- surface onboarding docs

Forge gives the user a LinkOS surface after each run. The packet is copied for the AI; LinkOS is rendered at the bottom of the Pythonista console for the human.

Forge is not background automation. It is a tight human-in-the-loop workflow.

## Setup

You need Pythonista on iOS or iPadOS.

1. Put this repository in your Pythonista Documents folder.
2. Open forge_entry.py in Pythonista.
3. Run it once.

On first run, if your clipboard does not contain a valid Forge bundle, Forge may return a failed-parse run packet. That is expected. The packet should still help orient you, and forge_entry.py should render LinkOS afterwards as the final console surface.

For a faster loop, create an iOS Shortcut that runs forge_entry.py, then pin that Shortcut somewhere convenient.

## Starting with an AI assistant

Open docs/AI_FIRST_BOOT.txt and paste it into a fresh AI chat.

That file tells the assistant how Forge works and tells it to ask you to run docs/MINIMAL_BOOT_BUNDLE.txt. Copy the boot bundle, run forge_entry.py, and paste the returned packet back.

After that, the assistant should guide you through Forge using docs, HELP, LinkOS, and the run packet.

## Useful first bundle

A good first bundle is:

LIST_FILES .
DEPTH: 2
FILES: yes

LIST_OPS

DOCS
OPEN: onboarding
SUGGEST: concepts, the-loop, run-packet, tutorial-loop, inspect-first, safe-patch

HELP DOCS

HELP LINKOS

Run that through Forge and paste the packet back to the assistant.

LinkOS should render automatically after the packet. You do not need to include a LINKOS op in the first bundle.

## Learning Forge

Forge includes docs and guides for the assistant to read and explain.

Important starting points:

- onboarding: start here
- concepts: key vocabulary
- the-loop: how the clipboard loop works
- run-packet: how to read Forge output
- tutorial: hands-on learning hub
- tutorial-loop: first practical lesson
- inspect-first: discovery before edits
- safe-patch: safer patching and recovery

For exact syntax, the assistant should use HELP followed by the op name.

For workflow guidance, it should use DOCS and the LinkOS surface rendered after each run.

## Recovery

Forge records run artifacts so you can recover from mistakes.

Useful recovery ops:

- LIST_RUNS: show recent runs
- DIFF <run_id>: inspect changes from a run
- REVERT_RUN <run_id>: restore files from a run snapshot
- BRANCH create <name>: checkpoint files before risky work

Before risky edits, the assistant should consider whether a branch is needed. For normal small documentation edits, branches are usually unnecessary.

## Core rule

Inspect before editing. Keep bundles small. Trust the run packet.
