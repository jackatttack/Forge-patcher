# Forge

Forge lets you pair-program with an AI assistant on your iPhone or iPad without giving the assistant direct filesystem access.

Forge is a local, clipboard-driven development harness for Pythonista on iOS. The assistant writes a plain-text Forge bundle. You choose when to run it. Forge executes it locally and returns a run packet.

The run packet is the source of truth.

## Why Forge exists

Most AI coding tools assume a desktop, a cloud workspace, or direct agent access.

Forge is different:

- local-first
- clipboard-driven
- human-in-the-loop
- packet-audited
- recoverable
- built for Pythonista on iPhone and iPad

The assistant can suggest actions, but Forge only runs what you copy and execute.

## The loop

1. The assistant writes a Forge bundle.
2. You copy it.
3. You run Forge locally in Pythonista.
4. Forge runs the bundle on your device.
5. Forge copies a run packet back to your clipboard.
6. You paste the packet back to the assistant.
7. The assistant reads the packet before suggesting the next step.

Nothing is confirmed until the packet comes back.

## Quick install

Create a new Pythonista file named:

    install_forge.py

Paste in the installer script from this repo and run it.

The installer downloads this repo and installs Forge into:

    ~/Documents/forge/

Then open and run:

    forge/forge_entry.py

## Start with an AI assistant

For a new user tutorial, paste this file into a fresh AI chat:

    forge/AI_FIRST_BOOT.txt

For a shorter experienced-user prompt, use:

    forge/AI_MINIMAL_BOOT.txt

## Optional root router

After installing, you can run:

    forge/install_root_router.py

That copies the current Forge entry script to:

    ~/Documents/forge_entry.py

Use this if you want an easy iOS Shortcut target and tappable Surface links.

## Core rule

Inspect before editing.

Keep bundles small.

Trust the packet.
