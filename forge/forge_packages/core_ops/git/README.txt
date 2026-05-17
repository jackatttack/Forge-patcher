GIT
===

GIT is Forge's GitHub release helper.

It talks to the GitHub API directly, which is useful on iOS because Pythonista does not need a local git command-line install.

Token safety
------------

GIT reads a token from a local file and never prints the token.

Default token file:

    forge2/private/github_token.txt

You can override it:

    GIT status
    TOKEN_FILE: forge/private/github_token.txt

Commands
--------

Status:

    GIT status

Lists repo, branch, visibility, URL, latest commit, and token state.

Branches:

    GIT branches

Commits:

    GIT commits
    LIMIT: 5

Files:

    GIT files
    PATH: forge

File:

    GIT file
    PATH: README.txt

Diff local file against remote:

    GIT diff
    LOCAL: forge/README.txt
    REMOTE: README.txt

Upload one file dry run:

    GIT upload
    LOCAL: forge/README.txt
    REMOTE: README.txt
    MESSAGE: Update README
    DRY_RUN: yes

Upload a folder dry run:

    GIT upload
    LOCAL: workspaces/forge_public_release
    REMOTE: .
    MESSAGE: Publish Forge release
    DRY_RUN: yes

Folder upload maps all files under LOCAL into REMOTE. Use REMOTE: . for repository root.

Folder upload skips generated artifacts, scratch files, private paths, caches, and secret-looking names.

Upload for real:

    GIT upload
    LOCAL: workspaces/forge_public_release
    REMOTE: .
    MESSAGE: Publish Forge release
    CONFIRM: yes

Delete dry run:

    GIT delete
    REMOTE: old/file.txt
    MESSAGE: Remove old file
    DRY_RUN: yes

Delete a folder dry run:

    GIT delete
    REMOTE: old_folder
    MESSAGE: Remove old release folder
    DRY_RUN: yes

Delete for real:

    GIT delete
    REMOTE: old/file.txt
    MESSAGE: Remove old file
    CONFIRM: yes

Folder delete recursively deletes every file under the remote folder.

Safety model
------------

Read-only commands do not require confirmation.

Upload and delete require either:

    DRY_RUN: yes

or:

    CONFIRM: yes

Recommended public release flow
-------------------------------

1. GIT status
2. GIT files
3. GIT delete old remote folders with DRY_RUN: yes if needed
4. GIT upload folder with DRY_RUN: yes
5. Repeat with CONFIRM: yes only after the dry-run looks right
6. GIT commits
