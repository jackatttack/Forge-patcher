CREATE_FILE is the reboot text-file creation op.

It creates or replaces a project-relative file and records before/after state in the run context so the storage layer can write snapshots for DIFF and REVERT_RUN.
