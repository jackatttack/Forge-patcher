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

### Quick install

Create a new Pythonista file named install_forge.py, paste the installer script from this repo, and run it.

The installer downloads the latest public Forge repo from GitHub and installs it into:

    Forge/

Then open:

    Forge/forge_entry.py

and run it once.

### Manual install

Download this repository from GitHub, place it in your Pythonista Documents folder, open forge_entry.py, and run it once.

On first run, if your clipboard does not contain a valid Forge bundle, Forge may return a failed-parse run packet. That is expected. The packet should still help orient you, and forge_entry.py should render LinkOS afterwards as the final console surface.

## Start with an AI assistant

Open docs/AI_FIRST_BOOT.txt and paste it into a fresh AI chat.

That file tells the assistant how Forge works and tells it to give you the minimal first bundle. Copy the bundle, run forge_entry.py, and paste the returned packet back.

A good first bundle is also saved at:

    docs/MINIMAL_BOOT_BUNDLE.txt

## Contained mode first

Forge works out of the box in contained mode.

Contained mode means Forge runs inside its own install folder. This is safest for first use.

LinkOS still renders in contained mode. Some console buttons may be display-only because Pythonista does not always resolve nested script links reliably. If a LinkOS button does not launch, just run forge_entry.py manually.

## Optional root router

When you are comfortable with Forge, you can enable root launcher mode by running:

    install_root_router.py

This creates small launcher files at Pythonista Documents root:

    forge_entry.py
    linkos.py

Benefits:

- tappable LinkOS console links
- easier Shortcut setup
- wider Pythonista Documents workspace access

Risk:

- Forge can inspect and patch more of your workspace

Only enable root launcher mode deliberately. Keep trusting the run packet and inspect before editing.

## Useful first bundle

    LIST_FILES .
    DEPTH: 2
    FILES: yes

    LIST_OPS

    DOCS
    OPEN: onboarding
    SUGGEST: concepts, the-loop, run-packet, tutorial-loop, inspect-first, safe-patch

    HELP DOCS

    HELP LINKOS

    HELP LIST_FILES

    HELP CREATE_FILE

    HELP RUN_FILE

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
- root-launcher-mode: optional root router and wider access

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

## Smoke test

Run this after install or update:

    forge_public_smoke.py

It checks important files and compiles the core public Forge scripts.

## Core rule

Inspect before editing. Keep bundles small. Trust the run packet.
