# -*- coding: utf-8 -*-
"""
Root launcher for the Forge dev harness.

This keeps forge as the real implementation while giving us
a stable root-level entry point for testing the reboot loop.

Shortcut behaviour:
- if a file path is passed, read that file as the bundle
- otherwise read the current iOS clipboard as the bundle
- run the reboot harness
- copy the full returned packet/surface text back to the clipboard
- also print it for Pythonista console visibility
"""

import importlib.util
import os
import json
import shlex
import sys


ROOT = os.path.abspath(os.path.expanduser('~/Documents'))


def _is_forge_home(path):
    path = os.path.abspath(str(path or ''))
    return (
        os.path.isfile(os.path.join(path, 'entry.py'))
        and os.path.isfile(os.path.join(path, 'forge_entry.py'))
        and os.path.isdir(os.path.join(path, 'forge_core'))
        and os.path.isdir(os.path.join(path, 'forge_packages'))
    )


def _candidate_forge_homes():
    here = os.path.abspath(os.path.dirname(__file__))
    docs = ROOT

    candidates = [
        here,
        os.path.join(here, 'Forge'),
        os.path.join(docs, 'Forge'),
        os.path.join(docs, 'forge'),
        os.path.join(docs, 'workspaces', 'forge_reboot'),
    ]

    env_home = os.environ.get('FORGE_HOME')
    if env_home:
        candidates.insert(0, env_home)

    seen = set()
    out = []
    for item in candidates:
        path = os.path.abspath(os.path.expanduser(str(item or '')))
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def _search_for_forge_home():
    docs = ROOT
    skip_names = set([
        '.Trash',
        '__pycache__',
        'site-packages',
        'site-packages-2',
        'artifacts',
        'archive',
        'Examples',
        'Templates',
    ])

    try:
        for dirpath, dirnames, filenames in os.walk(docs):
            rel = os.path.relpath(dirpath, docs)
            depth = 0 if rel == '.' else len(rel.split(os.sep))
            if depth >= 4:
                dirnames[:] = []

            dirnames[:] = [
                d for d in sorted(dirnames)
                if not d.startswith('.') and d not in skip_names
            ]

            if _is_forge_home(dirpath):
                return os.path.abspath(dirpath)
    except Exception:
        pass

    return ''


def _find_forge_home():
    for path in _candidate_forge_homes():
        if _is_forge_home(path):
            return path

    found = _search_for_forge_home()
    if found:
        return found

    return ''


FORGE_HOME = _find_forge_home()
if FORGE_HOME:
    os.environ['FORGE_HOME'] = FORGE_HOME

REBOOT_DIR = FORGE_HOME
ENTRY_PATH = os.path.join(REBOOT_DIR, 'entry.py') if REBOOT_DIR else ''


def _load_entry():
    for name in list(sys.modules.keys()):
        if (
            name == 'entry'
            or name.startswith('forge_core')
            or name.startswith('forge_reboot_core_op_')
        ):
            del sys.modules[name]

    if not REBOOT_DIR or not ENTRY_PATH:
        raise RuntimeError(
            'Could not find Forge home. Expected a folder containing entry.py, forge_entry.py, forge_core/, and forge_packages/.'
        )

    if not os.path.isfile(ENTRY_PATH):
        raise RuntimeError('Could not load Forge entry because entry.py is missing: %s' % ENTRY_PATH)

    os.environ['FORGE_HOME'] = REBOOT_DIR

    if REBOOT_DIR not in sys.path:
        sys.path.insert(0, REBOOT_DIR)

    spec = importlib.util.spec_from_file_location('forge_entry_runtime', ENTRY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('Could not load Forge entry: %s' % ENTRY_PATH)

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_from_text(bundle_text, mode='dev', store=True):
    entry = _load_entry()
    return entry.run_from_text(
        bundle_text,
        project_root=ROOT,
        mode=mode,
        store=store,
    )


def _read_clipboard():
    try:
        import clipboard
        value = clipboard.get()
    except Exception as e:
        raise RuntimeError('Could not read clipboard: %s: %s' % (type(e).__name__, e))

    if value is None:
        return ''
    return str(value)


def _write_clipboard(text):
    try:
        import clipboard
        clipboard.set(str(text))
        return True, ''
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)


def _format_output(run):
    run = run or {}
    packet = run.get('packet') or ''
    stamp = run.get('stamp') or '?'

    def clipboard_raw_return():
        """Return raw copied text when a CLIPBOARD op was applied.

        CLIPBOARD is intentionally different from normal Forge ops: its user-facing
        purpose is copying text, not returning a packet wrapper. The run is still
        stored on disk, but the iOS clipboard should contain the copied source.
        """
        results = run.get('results') or []
        chosen = None

        for result in results:
            if not isinstance(result, dict):
                continue
            op_name = str(result.get('op') or '').strip().upper()
            status = str(result.get('status') or '').strip().upper()
            if op_name == 'CLIPBOARD' and status == 'APPLIED':
                chosen = result

        if not chosen:
            return None

        data = chosen.get('data') or {}
        target = (
            chosen.get('file')
            or data.get('path')
            or chosen.get('target')
            or ''
        )
        target = str(target or '').strip().replace('\\', '/').lstrip('/')

        if not target:
            return None

        abs_path = os.path.abspath(os.path.join(ROOT, target))
        root_abs = os.path.abspath(ROOT)

        if not (abs_path == root_abs or abs_path.startswith(root_abs + os.sep)):
            return None

        if not os.path.isfile(abs_path):
            return None

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    raw_clipboard = clipboard_raw_return()
    if raw_clipboard is not None:
        return raw_clipboard

    parts = ['=== FORGE CLIPBOARD RETURN ===']

    if packet:
        parts.append(packet.rstrip())

    output = '\n'.join(parts).rstrip() + '\n'

    limit = 100000
    if len(output) <= limit:
        return output

    footer = [
        '',
        '=== OUTPUT TRUNCATED ===',
        'Clipboard return limited to %d chars for iOS Shortcut usability.' % limit,
        'Full run was still stored on disk.',
        '',
        'To inspect the full packet, run:',
        'RUNS show %s' % stamp,
        '',
        'Or inspect the run artifact inside the Forge install:',
        os.path.join(os.path.relpath(os.environ.get('FORGE_HOME') or REBOOT_DIR or '.', ROOT), 'artifacts', 'runs', str(stamp)),
    ]

    room = max(0, limit - len('\n'.join(footer)) - 2)
    return output[:room].rstrip() + '\n' + '\n'.join(footer).rstrip() + '\n'

def _latest_run_stamp():
    from forge_core.run_storage import list_runs
    runs = list_runs(ROOT, limit=1, mode='dev')
    return runs[0] if runs else ''


def _load_stored_run(stamp):
    from forge_core.run_storage import read_text

    stamp = str(stamp or '').strip()
    if not stamp or stamp == 'latest':
        stamp = _latest_run_stamp()

    if not stamp:
        return {}, ''

    text = read_text(ROOT, stamp, 'run.json')
    if not text:
        return {'stamp': stamp, 'missing': True, 'results': []}, stamp

    try:
        run = json.loads(text)
    except Exception:
        run = {'stamp': stamp, 'missing': True, 'results': []}

    if isinstance(run, dict) and not run.get('stamp'):
        run['stamp'] = stamp

    return run, stamp


def _handle_run_op(rest):
    """Fire a single-op bundle from a run_op route.

    rest layout: [parent_stamp, OP_NAME, target, DIRECTIVE=value, ...]

    Synthesises a bundle, runs it through the standard runner, stores
    in artifacts/runs_ephemeral/, then renders the new run's detail
    page for op #0.
    """
    if len(rest) < 2:
        print('=== run_op needs OP_NAME and target ===')
        return

    parent_stamp = str(rest[0] or '').strip()
    op_name = str(rest[1] or '').strip().upper()
    target = str(rest[2] or '').strip() if len(rest) > 2 else ''
    directive_tokens = list(rest[3:])

    lines = [op_name + (' ' + target if target else '')]
    for tok in directive_tokens:
        s = str(tok or '').strip()
        if '=' in s:
            k, _, v = s.partition('=')
            lines.append('%s: %s' % (k.strip().upper(), v.strip()))
    bundle = '\n'.join(lines) + '\n'

    _load_entry()
    try:
        from forge_core.runner import run_text
        from forge_core.surface.page_stack import build_run_page_stack
        from forge_core.surface.page_runtime import render_stack_page
    except Exception as e:
        print('=== run_op import failed: %s ===' % e)
        return

    project_root = ROOT
    try:
        os.environ['FORGE_HOME'] = REBOOT_DIR or os.environ.get('FORGE_HOME', '')
        run = run_text(bundle, project_root=project_root, mode='ephemeral', store=False)
    except Exception as e:
        print('=== run_op execution failed: %s: %s ===' % (type(e).__name__, e))
        return

    if isinstance(run, dict):
        run['parent_run'] = parent_stamp or None
        run['ephemeral'] = True
        run['stamp'] = run.get('stamp') or 'ephemeral'

    try:
        stack = build_run_page_stack(run, registry={})
        render_stack_page(stack, 'op.detail.0', parent_stamp)
    except Exception as e:
        print('=== run_op render failed: %s: %s ===' % (type(e).__name__, e))

def _safe_rel_for_pythonista(path):
    """Normalise a Pythonista/editor path route into a safe project-relative path.

    Route args can occasionally arrive as a list repr such as:
        ['forge/smoke.py']

    That should still resolve to:
        forge/smoke.py
    """
    if isinstance(path, (list, tuple)):
        if len(path) == 1:
            path = path[0]
        else:
            path = ' '.join(str(x) for x in path)

    path = str(path or '').strip()

    # Defensive cleanup for accidental list/tuple repr strings from route args.
    if (
        (path.startswith("['") and path.endswith("']"))
        or (path.startswith('["') and path.endswith('"]'))
        or (path.startswith("('") and path.endswith("',)"))
        or (path.startswith('("') and path.endswith('",)'))
    ):
        try:
            import ast
            parsed = ast.literal_eval(path)
            if isinstance(parsed, (list, tuple)) and parsed:
                path = str(parsed[0])
            elif isinstance(parsed, str):
                path = parsed
        except Exception:
            path = path.strip('[]()').strip().strip('"').strip("'")

    path = path.replace('\\', '/').lstrip('/')
    if not path:
        return ''

    norm = os.path.normpath(path).replace('\\', '/')
    if norm == '..' or norm.startswith('../') or os.path.isabs(norm):
        return ''
    return norm


def _flash_hud(message, kind='success'):
    try:
        import console
        console.hud_alert(str(message), kind, 0.8)
    except Exception:
        pass


def _handle_open_pythonista(path):
    """Open a project-relative file in the Pythonista editor.

    Also prints a tappable return surface so the console remains navigable after
    the editor opens.
    """
    rel = _safe_rel_for_pythonista(path)
    if not rel:
        _flash_hud('No file', 'error')
        print('No file path supplied.')
        try:
            _render_editor_return_surface('(no file)', stamp='latest')
        except Exception:
            pass
        return

    abs_path = os.path.join(ROOT, rel)
    if os.path.exists(abs_path):
        _flash_hud('Opening')
    else:
        _flash_hud('File missing', 'error')

    try:
        from urllib.parse import quote
    except Exception:
        from urllib import quote

    open_url = 'pythonista3://%s?action=open' % quote(rel, safe='/._-')

    try:
        import webbrowser
        webbrowser.open(open_url)
    except Exception as e:
        print('Open in Pythonista failed: %s: %s' % (type(e).__name__, e))
        print(open_url)

    try:
        _render_editor_return_surface(rel, stamp='latest')
    except Exception as e:
        print('')
        print('EDITOR')
        print('opened file')
        print('')
        print('Opened: %s' % rel)
        print('Return surface failed: %s: %s' % (type(e).__name__, e))

def _render_open_editor_return_surface(path, stamp='latest', return_page='run.audit', opened=True):
    """Small console surface shown after an editor-open action."""
    stamp = str(stamp or 'latest').strip() or 'latest'
    return_page = str(return_page or 'run.audit').strip() or 'run.audit'
    path = str(path or '').strip()

    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        doc_hero = None
        doc_text = None
        render_tile_dock = None

    title = 'EDITOR'
    subtitle = 'opened file' if opened else 'file missing'

    if doc_hero:
        doc_hero(title, subtitle)
    else:
        print('')
        print('EDITOR')
        print(subtitle)
        print('')

    if doc_text:
        if path:
            doc_text('Opened: %s' % path, tone='success' if opened else 'warning')
        else:
            doc_text('No file path supplied.', tone='warning')
        doc_text('Return controls are printed below so the console remains navigable.', tone='muted')
    else:
        if path:
            print('Opened: %s' % path)
        print('Return controls are printed below.')

    if return_page in ('landing', 'default', 'home', 'run.home'):
        back_route = ('run', stamp)
        back_label = 'Run'
        back_subtitle = 'landing'
    else:
        back_route = ('run_page', stamp, return_page)
        back_label = 'Back'
        back_subtitle = return_page.replace('run.', '').replace('op.', '')

    tiles = [
        ('⬅️ ', back_label, back_subtitle, back_route, 'warning'),
        ('▶ ', 'Run', 'landing', ('run', stamp), 'success'),
        ('📋 ', 'Audit', 'ops', ('run_page', stamp, 'run.audit'), 'accent'),
        ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
        ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
        ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
    ]

    if render_tile_dock:
        render_tile_dock('Return controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        print('')
        print('-- Return controls --')
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))

def _render_editor_return_surface(path, stamp='latest', back_page='run.audit'):
    """Render tappable return controls after opening a file in Pythonista."""
    path = _safe_rel_for_pythonista(path) or str(path or '').strip()
    stamp = str(stamp or 'latest').strip() or 'latest'
    back_page = str(back_page or 'run.audit').strip() or 'run.audit'

    try:
        _load_entry()
    except Exception:
        pass

    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text
        from forge_core.surface.render.tile_dock import render_tile_dock

        doc_hero('EDITOR', 'opened file')
        doc_text('Opened: %s' % (path or '(unknown)'), tone='text')
        doc_text('Return controls are printed below so the console remains navigable.', tone='muted')

        tiles = [
            ('⬅️ ', 'Back', 'audit', ('run_page', stamp, back_page), 'warning'),
            ('▶ ', 'Run', 'landing', ('run', stamp), 'success'),
            ('📋 ', 'Audit', 'ops', ('run_page', stamp, 'run.audit'), 'accent'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]
        render_tile_dock('Return controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
        return

    except Exception as e:
        print('')
        print('EDITOR')
        print('opened file')
        print('')
        print('Opened: %s' % (path or '(unknown)'))
        print('Return surface failed: %s: %s' % (type(e).__name__, e))
        print('')
        print('-- Return controls unavailable --')
        print('Run route manually if needed:')
        print('run latest')

def _handle_copy_text(rest):
    """Copy arbitrary text supplied by a route.

    Route shape:
        copy_text <label> <text...>
    """
    if not rest:
        print('No text supplied.')
        return

    label = str(rest[0] or 'text')
    text = ' '.join(str(x) for x in rest[1:]) if len(rest) > 1 else ''

    ok, err = _write_clipboard(text)
    if ok:
        _flash_hud('Copied %s' % label)
        print('Copied %s.' % label)
    else:
        _flash_hud('Copy failed', 'error')
        print('Copy failed: %s' % err)


def _handle_copy_path(path):
    """Copy a project-relative path."""
    rel = _safe_rel_for_pythonista(path)
    if not rel:
        print('No path supplied.')
        return

    ok, err = _write_clipboard(rel)
    if ok:
        _flash_hud('Path copied')
        print('Copied path: %s' % rel)
    else:
        _flash_hud('Copy failed', 'error')
        print('Copy failed: %s' % err)


def _handle_run_bundle(bundle_text):
    """Run a short Forge bundle from a tappable route."""
    bundle_text = str(bundle_text or '').strip()
    if not bundle_text:
        print('No bundle supplied.')
        return

    if not bundle_text.endswith('\n'):
        bundle_text += '\n'

    try:
        run = run_from_text(bundle_text, mode='dev', store=True)
    except Exception as e:
        print('run_bundle failed: %s: %s' % (type(e).__name__, e))
        return

    try:
        from forge_core.surface.page_stack import build_run_page_stack
        from forge_core.surface.page_runtime import render_landing
        stack = build_run_page_stack(run, registry={})
        render_landing(stack)
    except Exception as e:
        print('run_bundle render failed: %s: %s' % (type(e).__name__, e))


def _render_runs_index(limit=20):
    """Render recent useful dev runs as a first-class history surface."""
    _load_entry()

    try:
        from forge_core.run_storage import list_runs
        from forge_core.surface.render.docpage import doc_hero, doc_text
    except Exception as e:
        print('=== RUNS ROUTE FAILED ===')
        print('%s: %s' % (type(e).__name__, e))
        return True

    # Search deeper than the visible count. The visible Runs page is human
    # history, not raw artifact storage, so test/ephemeral runs are filtered.
    raw_names = list_runs(ROOT, limit=1000, mode='dev')
    useful = []

    for stamp in raw_names:
        run, resolved = _load_stored_run_for_history(stamp)
        stamp = resolved or stamp
        if _is_useful_history_run(run, stamp):
            useful.append((stamp, run))
        if len(useful) >= int(limit or 20):
            break

    try:
        latest = useful[0][0] if useful else ''
    except Exception:
        latest = ''

    try:
        doc_hero('RUNS', '%d useful run%s · tests hidden' % (
            len(useful),
            '' if len(useful) == 1 else 's',
        ))
    except Exception:
        print('')
        print('RUNS')
        print('%d useful run(s) · tests hidden' % len(useful))

    if not useful:
        try:
            doc_text('No useful dev runs found. Raw artifacts may still exist on disk.', tone='warning')
        except Exception:
            print('No useful dev runs found.')
        _runs_footer_controls()
        return True

    _runs_history_summary(useful)

    # Names come newest-first from storage. Print oldest-to-newest so the
    # newest useful run lands nearest the bottom of the console.
    for stamp, run in reversed(useful):
        _render_runs_history_card(stamp, run, latest=(stamp == latest))

    _runs_footer_controls()
    return True


def _runs_colour(tone):
    try:
        from forge_core.surface.render.primitives import colour
        colour(tone)
    except Exception:
        pass


def _runs_reset():
    try:
        from forge_core.surface.render.primitives import reset
        reset()
    except Exception:
        pass


def _runs_box_line(text='', tone='text', width=40):
    inner = width - 4
    text = str(text or '')
    if len(text) > inner:
        text = text[:max(0, inner - 1)] + '…'

    _runs_colour('audit.card.border')
    print('│ ', end='')
    _runs_reset()

    _runs_colour(tone)
    print(text.ljust(inner), end='')
    _runs_reset()

    _runs_colour('audit.card.border')
    print(' │')
    _runs_reset()


def _runs_box_rule(kind='top', width=40):
    if kind == 'top':
        text = '╭' + '─' * (width - 2) + '╮'
    elif kind == 'mid':
        text = '├' + '─' * (width - 2) + '┤'
    else:
        text = '╰' + '─' * (width - 2) + '╯'

    _runs_colour('audit.card.border')
    print(text)
    _runs_reset()


def _runs_box_wrapped(label, value, tone='text', width=40):
    import textwrap

    inner = width - 4
    label = str(label or '').strip()
    value = str(value or '').strip()
    if not value:
        return

    label_width = 8
    value_width = max(10, inner - label_width)
    wrapped = textwrap.wrap(value, width=value_width) or ['']

    for i, part in enumerate(wrapped):
        prefix = ('%-7s ' % (label + ':')) if i == 0 else ' ' * label_width
        _runs_box_line(prefix + part, tone=tone, width=width)


def _render_runs_box(stamp, status, label, tone, applied, skipped, failed, ops=None, message=''):
    width = 40
    print('')

    _runs_box_rule('top', width)
    _runs_box_line('%-24s %10s' % (str(label or 'RUN')[:24], _short_status(status).upper()[:10]), tone, width)
    _runs_box_rule('mid', width)

    _runs_box_wrapped('stamp', stamp, 'muted', width)
    _runs_box_wrapped('time', _friendly_run_stamp(stamp), 'text', width)
    _runs_box_wrapped('ops', '%s ok / %s skip / %s fail' % (applied, skipped, failed), 'audit.packet', width)

    if ops:
        _runs_box_wrapped('ran', ' · '.join(ops), 'text', width)

    if message:
        _runs_box_wrapped('note', message, 'audit.note', width)

    _runs_box_rule('bottom', width)

    _runs_card_outcome_graph(applied, skipped, failed)

def _load_stored_run_for_history(stamp):
    """Load a stored run for history filtering without routing side effects."""
    import json
    from forge_core.run_storage import read_text

    stamp = str(stamp or '').strip()
    if not stamp:
        return {}, ''

    try:
        text = read_text(ROOT, stamp, 'run.json') or ''
    except Exception:
        text = ''

    if not text:
        return {'stamp': stamp, 'missing': True, 'results': []}, stamp

    try:
        run = json.loads(text)
    except Exception:
        run = {'stamp': stamp, 'missing': True, 'results': []}

    if isinstance(run, dict) and not run.get('stamp'):
        run['stamp'] = stamp

    return run, stamp


def _is_useful_history_run(run, stamp=''):
    """True for runs that belong in the normal human Runs page.

    Keep this intentionally simple:
    - hide test runs
    - hide ephemeral child runs
    - keep dev runs, even if they contain diagnostic probes

    A dev run with a scratch probe is still usually useful history because it
    records the actual patch/inspection decision that happened.
    """
    run = run or {}
    mode = str(run.get('mode') or '').strip().lower()

    if mode in ('test', 'ephemeral'):
        return False

    if run.get('ephemeral') or run.get('parent_run'):
        return False

    # Legacy runs may not have mode recorded. Keep them unless they explicitly
    # claim to be some non-dev mode.
    if mode and mode != 'dev':
        return False

    return True


def _render_runs_history_card(stamp, run):
    """Render one run history card using the audit-card visual language."""
    run = run or {}
    results = run.get('results') or []
    counts = run.get('counts') or {}

    applied = counts.get('applied')
    skipped = counts.get('skipped')
    failed = counts.get('failed')

    if applied is None:
        applied = sum(1 for r in results if str((r or {}).get('status') or '').upper() == 'APPLIED')
    if skipped is None:
        skipped = sum(1 for r in results if 'SKIP' in str((r or {}).get('status') or '').upper())
    if failed is None:
        failed = sum(1 for r in results if 'FAIL' in str((r or {}).get('status') or '').upper())

    applied = applied or 0
    skipped = skipped or 0
    failed = failed or 0

    status = str(run.get('status') or 'RUN').upper()
    tone = 'success'
    title = 'RUN CLEAN'
    short = 'OK'
    if failed or 'FAIL' in status:
        tone = 'danger'
        title = 'RUN FAILED'
        short = 'FAIL'
    elif skipped or 'SKIP' in status:
        tone = 'warning'
        title = 'RUN PARTIAL'
        short = 'SKIP'

    ops = []
    for r in results[:5]:
        op = str((r or {}).get('op') or '?').upper()
        r_status = str((r or {}).get('status') or '?').upper()
        ops.append('%s %s' % (_status_glyph(r_status), op))
    if len(results) > 5:
        ops.append('+%d more' % (len(results) - 5))

    note = _first_run_message(results)
    if not note:
        note = '%d op%s' % (len(results), '' if len(results) == 1 else 's')

    rows = [
        ('stamp', stamp, 'audit.target'),
        ('time', _friendly_run_stamp(stamp), 'text'),
        ('ops', '%d ok / %d skip / %d fail' % (applied, skipped, failed), 'audit.packet'),
        ('ran', ' · '.join(ops), 'text'),
        ('note', note, 'audit.note'),
    ]

    _history_card(title, rows, status=short, tone=tone)
    _runs_card_outcome_graph(applied, skipped, failed)

    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
        render_tile_dock('Run actions', [
            ('▶ ', 'Open', 'landing', ('run', stamp), tone),
            ('📋 ', 'Audit', 'ops', ('run_page', stamp, 'run.audit'), 'accent'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
        ], cols=3, col_width=12, leading_space=1, trailing_space=1)
    except Exception:
        print('   Open / Audit / Raw')


def _history_card(title, rows=None, status='', tone='success'):
    import textwrap

    width = 40
    inner = width - 4
    label_width = 8
    value_width = inner - label_width

    def use_colour(name):
        try:
            from forge_core.surface.render.primitives import colour
            colour(name)
        except Exception:
            pass

    def clear_colour():
        try:
            from forge_core.surface.render.primitives import reset
            reset()
        except Exception:
            pass

    def frame(text):
        use_colour('audit.card.border')
        print(text)
        clear_colour()

    def content_line(text='', line_tone='text'):
        text = str(text or '')
        if len(text) > inner:
            text = text[:inner]

        use_colour('audit.card.border')
        print('│ ', end='')
        clear_colour()

        use_colour(line_tone)
        print(text.ljust(inner), end='')
        clear_colour()

        use_colour('audit.card.border')
        print(' │')
        clear_colour()

    def wrapped_rows(label, value, line_tone):
        label = str(label or '').strip()
        value = str(value or '').strip()
        if not value:
            return []
        wrapped = textwrap.wrap(value, width=max(10, value_width)) or ['']
        out = []
        for i, part in enumerate(wrapped):
            prefix = ('%-7s ' % (label + ':')) if i == 0 else ' ' * label_width
            out.append((prefix + part, line_tone))
        return out

    title = str(title or '').upper()
    status = str(status or '').upper()
    header = ('%-24s %10s' % (title[:24], status[:10])) if status else title[:inner]

    print('')
    frame('╭' + '─' * (width - 2) + '╮')
    content_line(header, tone)
    frame('├' + '─' * (width - 2) + '┤')

    printed = 0
    for row in rows or []:
        if len(row) == 2:
            label, value = row
            line_tone = 'text'
        else:
            label, value, line_tone = row
        for line, actual_tone in wrapped_rows(label, value, line_tone):
            content_line(line, actual_tone)
            printed += 1

    if not printed:
        content_line('(none)', 'muted')

    frame('╰' + '─' * (width - 2) + '╯')

def _runs_history_summary(useful):
    useful = list(useful or [])
    total = len(useful)
    failed = 0
    applied = 0
    latest = useful[0][0] if useful else ''
    oldest = useful[-1][0] if useful else ''

    for _stamp, run in useful:
        status = str((run or {}).get('status') or '').upper()
        if 'FAIL' in status:
            failed += 1
        elif status == 'APPLIED':
            applied += 1

    rows = [
        ('shown', '%d run%s' % (total, '' if total == 1 else 's'), 'accent'),
        ('clean', applied, 'success'),
        ('failed', failed, 'danger' if failed else 'muted'),
        ('latest', _friendly_run_stamp(latest), 'success'),
    ]
    if oldest and oldest != latest:
        rows.append(('oldest', _friendly_run_stamp(oldest), 'muted'))

    _runs_card_box('RUN HISTORY', rows, status='LIVE')


def _render_runs_history_card(stamp, run, latest=False):
    run = run or {}
    results = run.get('results') or []
    counts = run.get('counts') or {}

    status = str(run.get('status') or 'UNKNOWN').upper()
    applied = counts.get('applied')
    skipped = counts.get('skipped')
    failed = counts.get('failed')

    if applied is None:
        applied = sum(1 for r in results if str((r or {}).get('status') or '').upper() == 'APPLIED')
    if skipped is None:
        skipped = sum(1 for r in results if 'SKIP' in str((r or {}).get('status') or '').upper())
    if failed is None:
        failed = sum(1 for r in results if 'FAIL' in str((r or {}).get('status') or '').upper())

    applied = applied or 0
    skipped = skipped or 0
    failed = failed or 0

    tone = 'success' if status == 'APPLIED' else ('danger' if failed or 'FAIL' in status else 'warning')
    short_status = 'LATEST' if latest else ('FAIL' if tone == 'danger' else ('OK' if tone == 'success' else 'WARN'))

    ops = []
    for r in results[:5]:
        op = str((r or {}).get('op') or '?').upper()
        r_status = str((r or {}).get('status') or '?').upper()
        ops.append('%s %s' % (_status_glyph(r_status), op))

    if len(results) > 5:
        ops.append('+%d more' % (len(results) - 5))

    note = _first_run_message(results)
    packet_size = len(str(run.get('packet') or ''))

    rows = [
        ('stamp', stamp, 'audit.target'),
        ('time', _friendly_run_stamp(stamp), 'text'),
        ('status', status.lower(), tone),
        ('ops', '%d ok / %d skip / %d fail' % (applied, skipped, failed), tone),
    ]

    if ops:
        rows.append(('ran', ' · '.join(ops), 'audit.packet'))
    if note:
        rows.append(('note', note, 'audit.note'))
    if packet_size:
        rows.append(('packet', _format_bytes(packet_size), 'muted'))

    title = 'LATEST RUN' if latest else ('RUN FAILED' if tone == 'danger' else 'RUN CLEAN')
    _runs_card_box(title, rows, status=short_status)
    _runs_card_outcome_graph(applied, skipped, failed)
    _runs_card_actions(stamp, tone=tone, latest=latest)


def _runs_card_box(title, rows=None, status=''):
    import textwrap

    width = 40
    inner = width - 4
    label_width = 8
    value_width = inner - label_width

    def use_colour(tone):
        try:
            from forge_core.surface.render.primitives import colour
            colour(tone)
        except Exception:
            pass

    def clear_colour():
        try:
            from forge_core.surface.render.primitives import reset
            reset()
        except Exception:
            pass

    def frame(text):
        use_colour('audit.card.border')
        print(text)
        clear_colour()

    def content_line(text='', tone='text'):
        text = str(text or '')
        if len(text) > inner:
            text = text[:inner]

        use_colour('audit.card.border')
        print('│ ', end='')
        clear_colour()

        use_colour(tone)
        print(text.ljust(inner), end='')
        clear_colour()

        use_colour('audit.card.border')
        print(' │')
        clear_colour()

    def wrapped_rows(label, value, tone):
        label = str(label or '').strip()
        value = str(value or '').strip()
        if not value:
            return []

        wrapped = textwrap.wrap(value, width=max(10, value_width)) or ['']
        out = []
        for i, part in enumerate(wrapped):
            prefix = ('%-7s ' % (label + ':')) if i == 0 else ' ' * label_width
            out.append((prefix + part, tone))
        return out

    title = str(title or '').upper()
    status = str(status or '').upper()

    if status:
        header = ('%-24s %10s' % (title[:24], status[:10]))
    else:
        header = title[:inner]

    print('')
    frame('╭' + '─' * (width - 2) + '╮')
    content_line(header, 'success' if status in ('OK', 'APPLIED', 'LIVE', 'LATEST') else ('danger' if status == 'FAIL' else 'text'))
    frame('├' + '─' * (width - 2) + '┤')

    printed = 0
    for row in rows or []:
        if len(row) == 2:
            label, value = row
            tone = 'text'
        else:
            label, value, tone = row
        for line, line_tone in wrapped_rows(label, value, tone):
            content_line(line, line_tone)
            printed += 1

    if not printed:
        content_line('(none)', 'muted')

    frame('╰' + '─' * (width - 2) + '╯')


def _runs_card_actions(stamp, tone='accent', latest=False):
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    label = 'Latest actions' if latest else 'Run actions'
    tiles = [
        ('▶ ', 'Open', 'landing', ('run', stamp), tone),
        ('📋 ', 'Audit', 'ops', ('run_page', stamp, 'run.audit'), 'accent'),
        ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
    ]

    if render_tile_dock:
        render_tile_dock(label, tiles, cols=3, col_width=12, leading_space=1, trailing_space=1)
    else:
        print('')
        print('-- %s --' % label)
        for icon, name, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, name, subtitle))


def _format_bytes(value):
    try:
        value = int(value or 0)
    except Exception:
        value = 0

    if value < 1024:
        return '%d B' % value
    if value < 1024 * 1024:
        return '%.1f KB' % (float(value) / 1024.0)
    return '%.1f MB' % (float(value) / (1024.0 * 1024.0))

def _friendly_run_stamp(stamp):
    stamp = str(stamp or '').strip()
    # 20260514_081957 -> 14 May · 08:19:57
    try:
        date, time = stamp.split('_', 1)
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        hh = time[:2]
        mm = time[2:4]
        ss = time[4:6]
        return '%s-%s-%s · %s:%s:%s' % (year, month, day, hh, mm, ss)
    except Exception:
        return stamp


def _short_status(status):
    """Compact text status for older callers."""
    status = str(status or '').upper()
    if status == 'APPLIED':
        return 'ok'
    if 'FAIL' in status:
        return 'fail'
    if 'SKIP' in status:
        return 'skip'
    return status.lower()[:6]

def _status_glyph(status):
    """Tiny visual status marker for run history operation chips."""
    status = str(status or '').upper()
    if status == 'APPLIED':
        return '✓'
    if 'FAIL' in status:
        return '✕'
    if 'SKIP' in status:
        return '↷'
    return '•'


def _first_run_message(results):
    """Short note preview for run cards.

    Keep this deliberately compact. The Audit/Raw controls are the route to full
    detail, so the run card should not become a packet dump.
    """
    for r in results or []:
        msg = str((r or {}).get('message') or '').strip()
        if msg:
            msg = msg.split('\n')[0].strip()
            if len(msg) > 64:
                return msg[:61].rstrip() + '…'
            return msg
    return ''


def _runs_card_outcome_graph(applied, skipped, failed):
    """Compact per-run outcome graph for the runs history page."""
    try:
        applied = int(applied or 0)
    except Exception:
        applied = 0
    try:
        skipped = int(skipped or 0)
    except Exception:
        skipped = 0
    try:
        failed = int(failed or 0)
    except Exception:
        failed = 0

    values = [
        ('applied', applied, 'success'),
        ('skipped', skipped, 'warning'),
        ('failed', failed, 'danger'),
    ]
    max_value = max([v for _label, v, _tone in values] + [1])
    bar_width = 14

    print('   outcome:')
    for label, value, tone in values:
        if value > 0:
            filled = max(1, int(round((float(value) / float(max_value)) * bar_width)))
        else:
            filled = 0
        empty = max(0, bar_width - filled)
        bar = ('█' * filled) + ('░' * empty)
        line = '     %-7s %s  %s' % (label, bar, value)
        try:
            from forge_core.surface.render.primitives import say
            say(line, tone=tone if value else 'muted')
        except Exception:
            print(line)

def _print_wrapped_run_line(prefix, text, width=30):
    text = str(text or '').strip()
    prefix = str(prefix or '')
    if not text:
        return

    words = text.split()
    line = ''
    first = True

    for word in words:
        candidate = word if not line else line + ' ' + word
        if len(candidate) <= width:
            line = candidate
            continue

        if line:
            print((prefix if first else ' ' * len(prefix)) + line)
            first = False
        line = word

    if line:
        print((prefix if first else ' ' * len(prefix)) + line)


def _runs_footer_controls():
    """Bottom controls for the recent-runs index."""
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
        render_tile_dock('Footer controls', [
            ('↻ ', 'Refresh', 'runs', ('runs',), 'accent'),
            ('▶ ', 'Latest', 'landing', ('run', 'latest'), 'success'),
            ('📋 ', 'Latest audit', 'ops', ('run_page', 'latest', 'run.audit'), 'accent'),
            ('📦 ', 'Latest raw', 'packet', ('run_page', 'latest', 'packet.raw'), 'warning'),
            ('📖 ', 'Docs', 'guides', ('docs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ], cols=2, col_width=18, leading_space=1, trailing_space=2)
    except Exception:
        print('')
        print('-- Footer controls --')
        print('  Refresh runs')
        print('  Latest')
        print('  Latest audit')
        print('  Latest raw')
        print('  Docs')
        print('  Home')

def _render_route(argv):
    """Handle tappable LinkOS-style route args.

    Pythonista URLs may pass route args as either:
        ["run_page", "STAMP", "page.id"]
    or:
        ["run_page STAMP page.id"]

    Optional fourth arg:
        run_page STAMP page.id BACK_PAGE

    BACK_PAGE is the return target for contextual Back controls.
    """
    if not argv:
        return False

    if len(argv) == 1:
        raw = str(argv[0] or '').strip()
        if raw:
            try:
                argv = shlex.split(raw)
            except Exception:
                argv = raw.split()

    cmd = str(argv[0] or '').strip()

    # Direct utility routes.
    if cmd == 'open_pythonista':
        _handle_open_pythonista(argv[1:])
        return True
    if cmd == 'run_bundle':
        _handle_run_bundle(' '.join(argv[1:]) if len(argv) > 1 else '')
        return True
    if cmd == 'copy_text':
        _handle_copy_text(argv[1:])
        return True
    if cmd == 'copy_path':
        _handle_copy_path(' '.join(argv[1:]) if len(argv) > 1 else '')
        return True
    if cmd == 'run_op':
        _handle_run_op(argv[1:])
        return True

    # Routes below need the reboot workspace on sys.path.
    if cmd in ('docs', 'doc', 'copy_doc', 'copy_doc_bundle', 'runs', 'home', 'run', 'run_page'):
        _load_entry()
    else:
        return False

    # Docs routes.
    if cmd == 'docs':
        try:
            from forge_core.docs_surface import render_docs
            render_docs(ROOT, argv[1] if len(argv) > 1 else '')
        except Exception as e:
            print('=== DOCS ROUTE FAILED ===')
            print('%s: %s' % (type(e).__name__, e))
        return True

    if cmd == 'doc':
        try:
            from forge_core.docs_surface import render_doc
            render_doc(ROOT, argv[1] if len(argv) > 1 else '')
        except Exception as e:
            print('=== DOC ROUTE FAILED ===')
            print('%s: %s' % (type(e).__name__, e))
        return True

    if cmd == 'copy_doc':
        try:
            from forge_core.docs_surface import copy_doc
            copy_doc(ROOT, argv[1] if len(argv) > 1 else '')
        except Exception as e:
            print('=== COPY DOC FAILED ===')
            print('%s: %s' % (type(e).__name__, e))
        return True

    if cmd == 'copy_doc_bundle':
        try:
            from forge_core.docs_surface import copy_doc_bundle
            slug = argv[1] if len(argv) > 1 else ''
            index = argv[2] if len(argv) > 2 else '0'
            copy_doc_bundle(ROOT, slug, index)
        except Exception as e:
            print('=== COPY DOC BUNDLE FAILED ===')
            print('%s: %s' % (type(e).__name__, e))
        return True

    if cmd == 'runs':
        return _render_runs_index()

    try:
        from forge_core.surface.page_stack import build_run_page_stack
        from forge_core.surface.page_runtime import render_landing, render_stack_page
    except Exception as e:
        print('=== FORGE ROUTE FAILED ===')
        print('%s: %s' % (type(e).__name__, e))
        return True

    try:
        if cmd == 'home':
            stamp = 'latest'
            page_id = 'landing'
            back_page = ''
        elif cmd == 'run':
            stamp = argv[1] if len(argv) > 1 else 'latest'
            page_id = 'landing'
            back_page = ''
        else:
            stamp = argv[1] if len(argv) > 1 else 'latest'
            page_id = argv[2] if len(argv) > 2 else 'run.home'
            back_page = argv[3] if len(argv) > 3 else ''

        run, resolved = _load_stored_run(stamp)
        if isinstance(run, dict):
            run['stamp'] = resolved or run.get('stamp') or stamp or 'latest'

        stack = build_run_page_stack(run, registry={})

        if page_id in ('landing', 'default', '', 'home'):
            render_landing(stack)
        else:
            render_stack_page(stack, page_id, *argv[3:])
    except Exception as e:
        print('=== FORGE ROUTE FAILED ===')
        print('route: %s' % ' '.join(str(x) for x in argv))
        print('%s: %s' % (type(e).__name__, e))

    return True

def main():
    argv = list(sys.argv[1:])

    if _render_route(argv):
        return

    if argv:
        with open(argv[0], 'r', encoding='utf-8') as f:
            bundle = f.read()
    else:
        bundle = _read_clipboard()

    if not bundle.strip():
        output = (
            '=== FORGE ERROR ===\n'
            'No bundle text found.\n\n'
            'WHY: forge_entry.py expected a bundle from a file argument or the iOS clipboard.\n'
            'Forge home: %s\n'
            'NEXT:\n'
            '- Copy a Forge bundle to the clipboard.\n'
            '- Run forge_entry.py again.\n'
        ) % (REBOOT_DIR or '(not found)')
        _write_clipboard(output)
        print(output)
        return

    run = run_from_text(bundle, mode='dev', store=True)
    output = _format_output(run)

    ok, err = _write_clipboard(output)
    if not ok:
        output = output.rstrip() + '\n\n=== CLIPBOARD WRITE FAILED ===\n' + err + '\n'
        print(output)
        return

    print('=== FORGE ===')
    print('Run: %s' % (run.get('stamp') or '?'))
    print('Status: %s' % (run.get('status') or 'UNKNOWN'))
    print('Clipboard return copied.')
    print('')

    try:
        import importlib

        for name in list(sys.modules):
            if name == 'forge_core.surface.render' or name.startswith('forge_core.surface.render.'):
                del sys.modules[name]
        importlib.invalidate_caches()

        from forge_core.surface.page_stack import build_run_page_stack
        from forge_core.surface.page_runtime import render_landing

        stack = build_run_page_stack(run, registry={})
        render_landing(stack)
    except Exception as e:
        print('=== HUMAN SURFACE ===')
        print('[live LinkOS surface failed: %s]' % e)
        print(run.get('surface_text') or '')


if __name__ == '__main__':
    main()
