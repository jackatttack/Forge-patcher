RUN_FILE is the reboot Python script execution op.

Use it for tests, smoke scripts, probes, and local maintenance scripts.

Shape:

RUN_FILE path/to/script.py

Optional:

ARGS: --flag value

Safety rules:
- target must exist
- target must stay inside the project root
- target must be a .py file
- stdout and stderr are captured into the run packet
- non-zero SystemExit and uncaught exceptions fail the op

Preferred use:
- run PREVIEW before running unfamiliar scripts
- use RUN_FILE for reboot tests and smoke checks
- use SEARCH/PREVIEW to diagnose failures before patching
