# -*- coding: utf-8 -*-
"""
Render context helpers for Forge LinkOS pages.
"""

DEFAULT_WIDTHS = {
    'iphone': 40,
    'ipad_portrait': 64,
    'ipad_landscape': 88,
    'unknown': 40,
}

SIZE_WIDTH_HINTS = {
    'compact': 40,
    'card': 44,
    'full': None,
    'wide': 64,
    'dashboard': 88,
}


def render_context(mode='standard',
                   size='full',
                   width=None,
                   indent=0,
                   device_class='unknown',
                   route=None,
                   run_stamp=None,
                   page_stack=None,
                   source_package=None):
    device_class = str(device_class or 'unknown')
    size = str(size or 'full')
    mode = str(mode or 'standard')

    base_width = width
    if base_width is None:
        base_width = SIZE_WIDTH_HINTS.get(size)
    if base_width is None:
        base_width = DEFAULT_WIDTHS.get(device_class, DEFAULT_WIDTHS['unknown'])

    return {
        'mode': mode,
        'size': size,
        'width': int(base_width),
        'indent': int(indent or 0),
        'device_class': device_class,
        'route': route,
        'run_stamp': run_stamp,
        'page_stack': list(page_stack or []),
        'source_package': source_package,
    }


def context_for_page(page, **overrides):
    page = page or {}
    ctx = render_context(
        mode=page.get('mode') or 'standard',
        size=page.get('size') or 'full',
        source_package=page.get('source') or 'reboot',
    )
    for k, v in overrides.items():
        if v is not None:
            ctx[k] = v
    return ctx
