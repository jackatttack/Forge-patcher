# Forge

Forge is a local AI development harness for Pythonista on iOS.

It lets an AI assistant help inspect, patch, run, and recover code on your device while you stay in control. The assistant writes a plain-text Forge bundle. You choose when to run it. Forge executes it locally and returns a run packet.

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
3. You run `forge_entry.py` in Pythonista.
4. Forge runs the bundle locally.
5. Forge copies a run packet back to your clipboard.
6. You paste the packet back to the assistant.
7. The assistant reads the packet and decides the next safe step.

Nothing is confirmed until the packet comes back.

## Quick install

Create a new Pythonista file named:

    install_forge.py

Paste in the installer script from this repo and run it.

Then open:

    Forge/forge_entry.py

Run it once.

## Start with an AI assistant

Open this file and paste it into a fresh AI chat:

    AI_FIRST_BOOT.txt

That guide teaches the assistant how Forge works, how to stay packet-driven, and how to give you the first safe runnable bundle.

A docs copy also lives at:

    docs/AI_FIRST_BOOT.txt

## First safe files

These files are safe starting points:

    start_here.py
    install_health.py
    forge_public_smoke.py
    linkos.py
    AI_FIRST_BOOT.txt

`start_here.py` explains what Forge is.

`install_health.py` checks your install without changing files.

`forge_public_smoke.py` checks important files and syntax.

`linkos.py` opens the human-facing LinkOS surface.

## LinkOS

Forge also renders a human-facing console surface called LinkOS.

LinkOS helps you understand what happened, where you are, and what to do next. It provides docs, health checks, run views, recovery links, and safe exits.

## Contained mode first

Forge starts in contained mode.

Contained mode means Forge works inside its own install folder. This is the safest setup for first use.

Some LinkOS buttons may be display-only in contained mode. That is fine. You can still run `forge_entry.py` manually.

## Optional root router

When you want tappable LinkOS links and wider workspace access, run:

    install_root_router.py

This creates small launcher files at Pythonista Documents root.

Only enable this deliberately. Root mode gives Forge access to more of your workspace.

## Core rule

Inspect before editing.

Keep bundles small.

Trust the packet.
