# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.router
==============================

Small public/minimal LinkOS dispatcher.
"""


def _clean(argv):
    if argv is None:
        return ['home']
    if isinstance(argv, str):
        argv = argv.split()
    out = [str(x).strip() for x in (argv or []) if str(x).strip()]
    return out or ['home']


def dispatch(argv=None):
    """Dispatch a LinkOS route."""
    argv = _clean(argv)
    cmd = argv[0].lower()
    rest = argv[1:]

    if cmd in ('home', 'index', 'start-here'):
        from forge.extensions.linkos.pages.home import home
        home()
        return

    if cmd == 'docs':
        from forge.extensions.linkos.pages.docs import docs_page
        docs_page(rest[0] if rest else '')
        return

    if cmd == 'doc':
        from forge.extensions.linkos.pages.doc import doc_page
        doc_page(rest[0] if rest else '')
        return

    if cmd == 'doc_missing':
        from forge.extensions.linkos.pages.doc_missing import doc_missing_page
        doc_missing_page(rest[0] if rest else '', source='direct_route')
        return

    if cmd == 'help':
        from forge.extensions.linkos.pages.help import help_page
        help_page(rest[0] if rest else 'HELP')
        return

    if cmd == 'start':
        from forge.extensions.linkos.actions.start import start
        start()
        return

    if cmd == 'files':
        from forge.extensions.linkos.pages.files import files_panel
        files_panel(' '.join(rest) if rest else '.')
        return

    if cmd == 'runs':
        from forge.extensions.linkos.pages.runs import runs_page
        runs_page(rest[0] if rest else None)
        return

    if cmd == 'run':
        from forge.extensions.linkos.pages.run import run_page
        run_page(rest[0] if rest else None)
        return

    if cmd == 'safety':
        from forge.extensions.linkos.pages.safety import safety_page
        safety_page()
        return

    if cmd == 'copy_packet':
        from forge.extensions.linkos.actions.run_ops import copy_packet
        copy_packet(rest[0] if rest else 'latest')
        return

    if cmd == 'copy_summary':
        from forge.extensions.linkos.actions.run_ops import copy_summary
        copy_summary(rest[0] if rest else 'latest')
        return

    if cmd == 'copy_failure_detail':
        from forge.extensions.linkos.actions.run_ops import copy_failure_detail
        copy_failure_detail(rest[0] if rest else 'latest')
        return

    if cmd == 'print_packet':
        from forge.extensions.linkos.actions.run_ops import print_packet
        print_packet(rest[0] if rest else 'latest')
        return

    if cmd == 'revert_run':
        from forge.extensions.linkos.actions.safety_ops import revert_run
        revert_run(rest[0] if rest else 'latest')
        return

    if cmd == 'restore_branch':
        from forge.extensions.linkos.actions.safety_ops import restore_branch
        restore_branch(' '.join(rest) if rest else '')
        return

    if cmd == 'copy_path':
        from forge.extensions.linkos.actions.file_ops import copy_path
        copy_path(' '.join(rest) if rest else '.')
        return

    if cmd == 'quicklook':
        from forge.extensions.linkos.actions.file_ops import quicklook_file
        quicklook_file(' '.join(rest) if rest else '.')
        return

    if cmd == 'open_in':
        from forge.extensions.linkos.actions.file_ops import open_in_file
        open_in_file(' '.join(rest) if rest else '.')
        return

    if cmd == 'run_py':
        from forge.extensions.linkos.actions.file_ops import run_py_file
        run_py_file(' '.join(rest) if rest else '.')
        return

    if cmd == 'open_pythonista':
        from forge.extensions.linkos.actions.open_in_pythonista import open_in_pythonista
        open_in_pythonista(' '.join(rest) if rest else '')
        return

    if cmd == 'run_forge':
        from forge.extensions.linkos.actions.run_forge import run_forge
        run_forge()
        return

    if cmd == 'copy_doc':
        from forge.extensions.linkos.actions.doc_ops import copy_doc
        copy_doc(rest[0] if rest else '')
        return

    if cmd == 'copy_doc_bundle':
        from forge.extensions.linkos.actions.doc_ops import copy_doc_bundle
        copy_doc_bundle(
            rest[0] if len(rest) > 0 else '',
            rest[1] if len(rest) > 1 else '',
        )
        return

    from forge.extensions.linkos.pages.unknown import unknown_page
    unknown_page(cmd, rest)


def main(argv=None):
    dispatch(argv)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
