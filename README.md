# Forge

Forge lets you pair-program with an AI assistant on your iPhone or iPad without giving the assistant direct filesystem access.

Forge is a local, clipboard-driven development harness for Pythonista and compatible Python IDE environments on iOS. The assistant writes a plain-text Forge bundle. You choose when to run it. Forge executes it locally and returns a run packet.

The run packet is the source of truth.

## Why Forge exists

Most AI coding tools assume a desktop, a cloud workspace, or direct agent access.

Forge is different:

- local-first
- clipboard-driven
- human-in-the-loop
- packet-audited
- recoverable
- built for Python coding on iPhone and iPad

The assistant can suggest actions, but Forge only runs what you copy and execute.

## The loop

1. The assistant writes a Forge bundle.
2. You copy it.
3. You run Forge locally.
4. Forge runs the bundle on your device.
5. Forge copies a run packet back to your clipboard.
6. You paste the packet back to the assistant.
7. The assistant reads the packet before suggesting the next step.

Nothing is confirmed until the packet comes back.

## Quick install — Pythonista

Create a new Python file in Pythonista, paste this in and run it once:

    from urllib.request import urlopen

    url = (
        'https://raw.githubusercontent.com/'
        'jackatttack/Forge-patcher/main/install_forge.py'
    )
    source = urlopen(url).read()
    exec(compile(source, 'install_forge.py', 'exec'))

The installer downloads the public Forge release and installs it into:

    ~/Documents/forge/

Existing Forge installs are backed up before replacement.

You can also read [`install_forge.py`](install_forge.py) before running it.

When installation finishes, open and run:

    forge/forge_entry.py

## Quick install — Python IDE on iOS

Python IDE exposes a writable `Workspace` plus a Pythonista-compatible `clipboard` module. Forge has a dedicated adapter for that environment so it does not rely on Pythonista's `~/Documents` path.

From the Python IDE Workspace, create a small installer file with:

    from urllib.request import urlopen

    url = (
        'https://raw.githubusercontent.com/'
        'jackatttack/Forge-patcher/main/install_pythonide.py'
    )
    source = urlopen(url).read()
    exec(compile(source, 'install_pythonide.py', 'exec'))

Run it once. It installs:

    Workspace/forge/
    Workspace/forge_entry.py

Then the normal loop is simply:

    python3 forge_entry.py

`forge_entry.py` reads the Forge bundle from the iOS clipboard, runs it against the Python IDE Workspace, copies the Forge return packet back to the clipboard, and prints the same packet in the terminal.

Existing Forge installs and root entry points are backed up before replacement. The installer also performs a clipboard round-trip check and a non-mutating Forge smoke test.

You can read [`install_pythonide.py`](install_pythonide.py) before running it.

## Start with an AI assistant

For a new user tutorial, paste this file into a fresh AI chat:

    forge/AI_FIRST_BOOT.txt

For a shorter experienced-user prompt, use:

    forge/AI_MINIMAL_BOOT.txt

## Optional root router

On Pythonista, after installing, you can run:

    forge/install_root_router.py

That copies the current Forge entry script to:

    ~/Documents/forge_entry.py

Use this if you want an easy iOS Shortcut target and tappable Surface links.

Python IDE's dedicated installer already creates its root `forge_entry.py`, so this extra router step is not needed there.

## Core rule

Inspect before editing.

Keep bundles small.

Trust the packet.
