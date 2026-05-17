MOVE is the reboot file move op.

Use it when a file should be renamed or relocated inside the project root.

Shape:

MOVE source/path.txt
TO: destination/path.txt

Optional:

OVERWRITE: yes

Safety rules:
- source must exist
- source and destination must remain inside the project root
- destination parent directories may be created
- existing destinations are blocked unless OVERWRITE: yes is present
- both source and destination states are recorded for REVERT_RUN

Preferred use:
- use MOVE for renames and file relocation
- use COPY when duplication is intended
- use REPLACE_FILE or REPLACE for content changes
