REPLACE_FILE is the reboot full-file replacement op.

It intentionally only replaces existing files. Use CREATE_FILE for new files.

Safety contract:
- target must stay inside project root
- body is required
- missing files fail before mutation
- unchanged files skip
- successful replacement records before/after touched metadata for DIFF and REVERT_RUN
