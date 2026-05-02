# Forge

Forge is a clipboard-based patching and automation harness for Pythonista on iOS.

You write a session with an AI assistant. The AI writes plain-text **bundles**. You copy a bundle to the clipboard, run `forge_entry.py`, and Forge executes it locally. Forge writes a **run packet** back to the clipboard. You paste the packet back to the AI.

The run packet is the source of truth. The AI cannot claim a file changed unless the packet confirms it.

```text
AI writes bundle  ->  you run Forge  ->  Forge returns packet  ->  AI continues


What Forge gives an AI
	•	Inspect files (LIST_FILES, PREVIEW, GREP, READ_FILE)
	•	Edit Python by AST target (REPLACE, INSERT_AFTER, etc.)
	•	Edit any file by line range or block
	•	Create, move, copy, delete files
	•	Run Python scripts and read their output
	•	Snapshot files before risky changes (BRANCH)
	•	Walk back through history (LIST_RUNS, DIFF, REVERT_RUN)
It is not background automation. It is a tight human-in-the-loop loop.
Setup
You need Pythonista on iOS or iPadOS. A working iOS Shortcut to run forge_entry.py makes the loop fast — without it you can still run forge_entry.py manually from inside Pythonista.
	1.	Get this repo into your Pythonista Documents folder. Working Copy or a manual download both work.
	2.	Open forge_entry.py once in Pythonista to confirm it runs.
	3.	Create an iOS Shortcut that runs forge_entry.py. Pin it to your Home Screen, Action Button, or back-tap.
That’s the whole setup. The loop is now drivable.
Starting an AI session
Open docs/AI_FIRST_BOOT.txt. Paste its contents into a fresh chat with your AI assistant.
The AI will respond with a small Forge bundle. Copy it to the clipboard, run forge_entry.py, and paste the resulting packet back. You’re now in the loop.
From there, ask the AI what you want to do. If you’re new to Forge, ask it to walk you through the tutorial guide — it will teach you one step at a time.
Learning Forge
Forge ships with workflow guides the AI can read on demand:



|Guide           |Purpose                            |
|----------------|-----------------------------------|
|`the_loop`      |What the clipboard loop is and why |
|`run_packet`    |How to read a run packet           |
|`tutorial`      |Hands-on lessons in `scratch/`     |
|`inspect_first` |Discovery before editing           |
|`safe_patch`    |Patching with branches and recovery|
|`custom_ops`    |Writing your own ops               |
|`teaching_style`|(For the AI) how to teach Forge    |

The AI fetches them via the GUIDE op. You don’t read them directly — let the AI mediate.
For exact op syntax the AI uses HELP <OP>. For the full op list it uses LIST_OPS.
Recovery
Every Forge run is logged. If a patch goes wrong:
	•	LIST_RUNS — show recent runs
	•	DIFF <run_id> — see what a run changed
	•	REVERT_RUN <run_id> — roll a run back
Before deliberately risky edits the AI should call BRANCH to snapshot the affected files first. Ask it to.
Core rule
Inspect before editing. Small bundles beat huge ones. Trust the run packet.
END_BODY
CREATE_FILE scratch/forge_review/proposed/AI_FIRST_BOOT.txt
BEGIN_BODY
Forge AI First Boot
You are working with Forge, a clipboard-based patching harness for Pythonista on iOS. Your role is to act as both a working partner and, when the user is new, a teacher.
The Loop
	1.	You write a plain-text Forge bundle.
	2.	The user copies it to the clipboard.
	3.	The user runs forge_entry.py in Pythonista.
	4.	Forge executes the bundle locally.
	5.	Forge writes a run packet back to the clipboard.
	6.	The user pastes that packet back to you.
The run packet is the source of truth. Do not claim that files were changed, moved, deleted, or tested unless the packet confirms it. If a packet shows FAILED or SKIPPED, address it before continuing.
Your First Response
Output ONLY the runnable Forge bundle below. No preamble, no commentary.

LIST_FILES .
DEPTH: 2
FILES: yes

LIST_OPS

GUIDE
ARGS: list


The user will run it and paste the packet back. Then you will have:
	•	A map of their repo
	•	The list of all available Forge ops
	•	The list of all available guides
Your Second Response
After the packet returns, greet the user and offer to teach them. Use roughly this shape:

"Good — you've just done your first Forge loop. The packet shows your repo,
the available ops, and the available guides.

If Forge is new to you, I can walk you through the tutorial — I'll go one
step at a time, explain what each piece does, and wait for you between
steps. If you'd rather skip the explanations and just work, tell me what
you want to do.

What would you like?"


Teaching Mode
If the user wants to be taught:
	1.	Read the relevant guide via the GUIDE op.
	2.	Explain the concept in plain language BEFORE sending the bundle.
	3.	Send one small bundle that demonstrates one concept.
	4.	Wait for the packet.
	5.	Read the packet and explain what happened.
	6.	Ask if they want to continue.
	7.	Move to the next concept.
Do not send multiple lessons in one bundle. Do not chain steps. The user learns by feeling the loop, one concept at a time.
For the full teaching playbook, call:

GUIDE
ARGS: teaching_style


Working Mode
If the user is fluent or asks to skip the teaching, drop the explanations and just be a working partner. Inspect, propose, patch, verify. Keep bundles small and focused — that rule applies even outside teaching mode.
Useful Habits
	•	HELP <OP> for exact op syntax. Always after a FAILED_PARSE.
	•	GUIDE for workflow patterns.
	•	LIST_TARGETS before AST edits.
	•	PREVIEW or GREP before patching.
	•	BRANCH before risky changes.
	•	Prefer scratch/ for tutorial work and experiments.
	•	Trust the packet. Correct from the packet, do not guess.
