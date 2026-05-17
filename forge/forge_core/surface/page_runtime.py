# -*- coding: utf-8 -*-
"""
Minimal LinkOS-style page runtime for Forge.
"""


def _render_accepts_context(render):
    try:
        code = getattr(render, '__code__', None)
        if code is None:
            return True
        return int(code.co_argcount) >= 2
    except Exception:
        return True


def _rule(width=42, char='─'):
    print(str(char) * int(width))


def _control_label(control):
    icon = str((control or {}).get('icon') or '')
    label = str((control or {}).get('label') or '')
    return (icon + label).strip()


def _control_target(control):
    control = control or {}
    route = control.get('route')
    action = control.get('action')
    value = control.get('value')

    if route:
        if isinstance(route, (list, tuple)):
            return 'LINKOS / ARGS: ' + ' '.join(str(x) for x in route)
        return 'LINKOS / ARGS: ' + str(route)

    if action:
        return 'action: ' + str(action)

    if value is not None:
        return 'value: ' + str(value)

    return ''


def render_control_panel(panel, context=None):
    panel = panel or {}
    controls = panel.get('controls') or []
    if not controls:
        return False

    title = str(panel.get('title') or panel.get('id') or 'Controls')
    _rule()
    print(title)
    _rule()

    for c in controls:
        label = _control_label(c)
        target = _control_target(c)
        note = str((c or {}).get('note') or '')

        if target:
            print('  %-18s %s' % (label[:18], target))
        else:
            print('  ' + label)

        if note:
            print('    ' + note)

    return True


def render_controls(page, context=None, placement=None):
    from forge_core.surface.control_model import sort_panels

    page = page or {}
    panels = sort_panels(page.get('controls') or [])
    if placement:
        panels = [p for p in panels if str(p.get('placement') or '') == str(placement)]

    rendered = False
    for panel in panels:
        if render_control_panel(panel, context):
            rendered = True
            print('')
    return rendered


def render_page(page, context=None, include_controls=True):
    page = page or {}
    context = context or {}

    render = page.get('render')
    if callable(render):
        if _render_accepts_context(render):
            render(page, context)
        else:
            render(page)
    else:
        print('=== REBOOT PAGE ===')
        print('id:', page.get('id') or '?')
        print('title:', page.get('title') or '?')
        print('kind:', page.get('kind') or '?')
        print('mode:', page.get('mode') or '?')
        print('size:', page.get('size') or '?')
        print('source:', page.get('source') or '?')

    if not include_controls:
        return True

    # Op detail pages and page-owned renderers usually own their own bottom
    # control strip. Do not append a second generic ACTIONS/NAVIGATION rail.
    if str(page.get('kind') or '') == 'op_detail':
        return True

    data = page.get('data') or {}
    page_allows_runtime_controls = data.get('runtime_controls', True)

    if not page_allows_runtime_controls:
        return True

    render_controls(page, context)

    try:
        from forge_core.surface.render.docpage import doc_tile_grid
        run_stamp = context.get('run_stamp') or data.get('stamp') or 'latest'
        doc_tile_grid('controls', [
            ('⬅️ ', 'Back', 'run landing', ('run', run_stamp), 'orange'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ])
    except Exception:
        pass

    return True

def _context_for(stack, page):
    from forge_core.surface.render_context import context_for_page
    from forge_core.surface.surface_plan import plan_surface

    stack = stack or {}
    run = stack.get('run') or {}
    pages = stack.get('pages') or []

    ctx = context_for_page(
        page,
        run_stamp=run.get('stamp') or 'latest',
        page_stack=pages,
    )

    plan = stack.get('surface_plan')
    if plan is None:
        plan = plan_surface(run, pages)

    if isinstance(ctx, dict):
        ctx['surface_plan'] = plan

    return ctx


def render_landing(stack):
    stack = stack or {}
    landing = stack.get('landing')
    pages = list(stack.get('pages') or [])

    def visible_surface(p):
        if not isinstance(p, dict):
            return False
        if p is landing:
            return False
        if not p.get('render_in_stack', True):
            return False

        page_id = str(p.get('id') or '')
        kind = str(p.get('kind') or '')
        source = str(p.get('source') or '')

        if page_id in ('packet.raw', 'run.docs', 'op.list', 'run.audit'):
            return False
        if page_id.startswith('op.detail.') or page_id.startswith('op.'):
            return False

        if kind in ('result', 'summary', 'preview') and source != 'reboot':
            return True

        if p.get('promote') and source != 'reboot':
            return True

        return False

    def alias_page_id(value):
        value = str(value or '').strip()
        aliases = {
            'summary': 'run.home',
            'home': 'run.home',
            'run.summary': 'run.home',
            'run': 'run.home',
            'ops': 'op.list',
            'op': 'op.list',
            'raw': 'packet.raw',
            'packet': 'packet.raw',
            'files': 'files.tree.0',
            'tree': 'files.tree.0',
            'audit': 'run.audit',
            'docs': 'run.docs',
        }
        return aliases.get(value, value)

    def stack_items(surface):
        raw = surface.get('stack') or ''
        if isinstance(raw, str):
            return [alias_page_id(x.strip()) for x in raw.replace(',', ' ').split() if x.strip()]

        out = []
        for item in raw or []:
            out.append(alias_page_id(item))
        return out

    def should_inline(page_id, explicit=False):
        page_id = alias_page_id(page_id)

        if page_id in (
            'landing',
            'default',
            'home',
            'packet.raw',
            'op.list',
            'run.docs',
        ):
            return False

        if page_id.startswith('files.tree.'):
            return False

        return True

    def render_direct_page(page, already):
        if not page:
            return False
        page_id = str(page.get('id') or '')
        if not page_id or page_id in already:
            return False

        ctx = _context_for(stack, page)
        ctx['stack_mode'] = True
        ctx['chrome'] = 'compact'
        render_page(page, ctx, include_controls=False)
        already.add(page_id)
        return True

    def render_stack_item(page_id, already, explicit=False):
        page_id = alias_page_id(page_id)
        if not page_id:
            return False
        if page_id in already:
            return False
        if not should_inline(page_id, explicit=explicit):
            return False

        page = find_page(stack, page_id)
        if not page:
            return False

        return render_direct_page(page, already)

    run = stack.get('run') or {}
    surface = run.get('surface') or {}
    rendered = set()

    from forge_core.surface.surface_plan import plan_surface
    plan = stack.get('surface_plan') or plan_surface(run, pages)

    focus_page = plan.get('focus_page')
    if focus_page:
        render_direct_page(focus_page, rendered)

    if plan.get('controlled'):
        for page in plan.get('inline_pages') or []:
            render_direct_page(page, rendered)
    else:
        requested_stack = stack_items(surface)
        for page_id in requested_stack:
            render_stack_item(page_id, rendered, explicit=True)

        promoted = [p for p in pages if visible_surface(p)]
        for page in promoted:
            render_direct_page(page, rendered)

        focus_id = alias_page_id(str(surface.get('focus') or '').strip())
        if focus_id and focus_id not in rendered:
            focus_page = find_page(stack, focus_id)
            if focus_page:
                render_direct_page(focus_page, rendered)
            else:
                render_stack_item(focus_id, rendered, explicit=True)

        audit_page = find_page(stack, 'run.audit')
        if audit_page and 'run.audit' not in rendered:
            render_direct_page(audit_page, rendered)

    if not landing:
        print('No landing page.')
        return False

    if plan.get('controlled'):
        if rendered:
            print('')
            print('──────── Navigation ────────')
        ctx = _context_for(stack, landing)
        ctx['controls_only'] = True
        ctx['chrome'] = 'compact'
        return render_page(landing, ctx, include_controls=False)

    if rendered:
        print('')
        print('──────── Run ────────')

    return render_page(landing, _context_for(stack, landing), include_controls=False)

def find_page(stack, page_id):
    wanted = str(page_id or '')
    for page in (stack or {}).get('pages') or []:
        if str(page.get('id') or '') == wanted:
            return page
    return None


def render_stack_page(stack, page_id, *trailing, back_page=''):
    """Render a single page out of the stack.

    Trailing positional args are route tokens. Two kinds:
        key=value   -> context['params'][key] = value
        other       -> context['back_page'] (last one wins)

    back_page may also be passed as a keyword for backwards compatibility
    with the original signature. If both are present, the explicit kwarg
    wins.

    Example route from a detail page pill:

        ('run_page', stamp, page_id, 'depth=3', 'run.audit')

    lands as render_stack_page(stack, page_id, 'depth=3', 'run.audit')
    producing context['params'] = {'depth': '3'} and
    context['back_page'] = 'run.audit'.
    """
    params = {}
    trailing_back = ''
    for token in trailing:
        s = str(token or '').strip()
        if not s:
            continue
        if '=' in s:
            key, _, value = s.partition('=')
            key = key.strip()
            if key:
                params[key] = value.strip()
        else:
            trailing_back = s

    effective_back = str(back_page or '').strip() or trailing_back

    page = find_page(stack, page_id)
    if page:
        ctx = _context_for(stack, page)
        if effective_back:
            ctx['back_page'] = effective_back
        if params:
            ctx['params'] = params
        return render_page(page, ctx)

    run = (stack or {}).get('run') or {}
    stamp = (stack or {}).get('stamp') or run.get('stamp') or 'latest'
    page_id = str(page_id or '')

    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text
        from forge_core.surface.render.tile_dock import render_tile_dock

        doc_hero('Page missing', page_id)
        doc_text(
            'This generated page is not available in the selected run stack.',
            tone='warning',
        )

        tiles = [
            ('⬅️ ', 'Back', 'run landing', ('run', stamp), 'orange'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('⚙ ', 'Ops', 'op list', ('run_page', stamp, 'op.list'), 'cyan'),
            ('📦 ', 'Raw', 'source packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]
        render_tile_dock('recovery', tiles, cols=2, col_width=18, row_gap=1, leading_space=1, trailing_space=2)
        return False
    except Exception:
        print('Page not found: %s' % page_id)
        print('')
        print('Try:')
        print('LINKOS')
        print('ARGS: run %s' % stamp)
        return False

def render_page_index(stack):
    page = find_page(stack, 'page.index')
    if page:
        return render_page(page, _context_for(stack, page))

    stack = stack or {}
    pages = stack.get('pages') or []
    print('Pages')
    print('-----')
    for i, page in enumerate(pages, 1):
        marker = '*' if page is stack.get('landing') else ' '
        print('%s %d. %s  [%s/%s/%s]' % (
            marker,
            i,
            page.get('id') or '?',
            page.get('kind') or '?',
            page.get('mode') or '?',
            page.get('size') or '?',
        ))
    return True


def render_full_stack(stack):
    stack = stack or {}
    for page in stack.get('pages') or []:
        print('')
        print('──────── %s ────────' % (page.get('id') or '?'))
        render_page(page, _context_for(stack, page))
    return True


def stack_for_run_dict(run):
    from forge_core.surface.page_stack import build_run_page_stack
    return build_run_page_stack(run or {}, registry={})


def render_run_dict(run, page_id='landing'):
    stack = stack_for_run_dict(run)
    if str(page_id or '') in ('landing', 'default', '', 'home'):
        return render_landing(stack)
    if str(page_id or '') in ('all', 'stack', 'full'):
        return render_full_stack(stack)
    return render_stack_page(stack, page_id)
