CLIPBOARD is the reboot clipboard bridge.

Use it when a generated file, starter bundle, handoff note, or export text needs to be copied back to the iOS clipboard.

Shape:

CLIPBOARD path/to/file.txt

Safety rules:
- target must be a file inside the project root
- file must exist
- body content is forbidden
- CLIPBOARD is read-only with respect to project files
- the only side effect is setting the iOS clipboard

Preferred use:
- use CLIPBOARD for handoff files and generated bundles
- use PREVIEW when you only need to inspect file content
- use EXPORT later when packing multiple files into a distributable artifact
