
# -*- coding: utf-8 -*-
"""
ops.url
=======
HTTP client op — gives the agent internet access.

Modes
-----
fetch     GET a URL and return body as text. HTML is stripped by default.
probe     HEAD request — returns status, headers, redirect chain.
download  Fetch binary content and save to DEST path.
json      GET + parse JSON. Optional JPATH for key extraction.

Directives
----------
MODE: fetch | probe | download | json   (default: fetch)
STRIP: no | plain | markdown            (fetch mode only, default: markdown)
DEST: path/to/file                      (download mode only)
HEADERS: Key=Value                      (repeatable — one per line)
TIMEOUT: 30                             (seconds, default: 30)
FOLLOW_REDIRECTS: yes | no              (default: yes)
JPATH: results.0.title                  (json mode — dot-path extraction)

$OUT fields
-----------
All modes:   status_code, content_type, url (final after redirects)
fetch:       stdout (text content)
probe:       stdout (summary), redirect_chain, server, content_length
download:    dest (path written), size, stdout (summary)
json:        stdout (pretty or extracted value)
"""

import json
import os
import re
import threading
import urllib.request
import urllib.error
import urllib.parse

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'URL',
    'target_kind': 'url',
    'body_mode': 'forbidden',
    'allowed_directives': set([
        'MODE', 'STRIP', 'DEST', 'HEADERS', 'TIMEOUT',
        'FOLLOW_REDIRECTS', 'JPATH', 'METHOD', 'BODY_DATA', 'CONTENT_TYPE',
    ]),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP URL.
HELP = {
    'summary': 'HTTP client — fetch, probe, download, parse JSON, or send POST/PUT/PATCH/DELETE requests.',
    'subject': ['Full URL including scheme, e.g. https://example.com'],
    'directives': [
        'MODE: fetch | probe | download | json  (default: fetch)',
        'METHOD: GET | POST | PUT | PATCH | DELETE  (default: GET; write verbs override MODE routing)',
        'STRIP: no | plain | markdown  (fetch mode only, default: markdown)',
        'DEST: path/to/file  (download mode — relative to project root)',
        'HEADERS: Key=Value  (one per line, repeatable)',
        'TIMEOUT: 30  (seconds, default: 30)',
        'FOLLOW_REDIRECTS: yes | no  (default: yes)',
        'JPATH: results.0.title  (json mode — dot-path extraction into $OUT.stdout)',
        'BODY_DATA: {"key": "value"}  (POST/PUT/PATCH body as string)',
        'CONTENT_TYPE: application/json  (default: application/json)',
    ],
    'common_failures': [
        'URL missing scheme (must start with https:// or http://).',
        'DEST required for download mode.',
        'JPATH key not found in JSON response.',
        'Timeout after 30 seconds — increase TIMEOUT for slow endpoints.',
        'Network unavailable on device.',
        'POST body rejected — check CONTENT_TYPE matches server expectation.',
        'Write methods (POST/PUT/PATCH/DELETE) override MODE routing.',
    ],
    'safe_usage': [
        'Use probe mode first to check a URL before fetching.',
        'Use STRIP: markdown for LLM-readable page content.',
        'Use json mode for APIs — pipe $OUT.stdout to JOURNAL or FLASHCARD.',
        'DEST path is relative to project root for download mode.',
        'Set METHOD: POST with BODY_DATA for REST API writes.',
        'Use HEADERS: Authorization=Bearer <token> for authenticated endpoints.',
        'JPATH supports dot-path and index access: results.0.title',
        '$OUT fields: stdout, status_code, content_type, url, size, dest, redirect_chain.',
    ],
    'minimal_example': [
        '# Fetch and strip a webpage',
        'URL https://example.com',
        'MODE: fetch',
        '',
        '# Probe headers and redirects',
        'URL https://example.com',
        'MODE: probe',
        '',
        '# Download a file',
        'URL https://example.com/file.pdf',
        'MODE: download',
        'DEST: downloads/file.pdf',
        '',
        '# Parse JSON with key extraction',
        'URL https://api.github.com/repos/python/cpython',
        'MODE: json',
        'JPATH: stargazers_count',
        '',
        '# POST to an API',
        'URL https://api.example.com/items',
        'METHOD: POST',
        'BODY_DATA: {"name": "test"}',
        'HEADERS: Authorization=Bearer mytoken',
    ],
    'related_ops': ['RUN_FILE', 'READ_FILE', 'JOURNAL', 'FLASHCARD'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'target': 'Provide a full URL — e.g. URL https://example.com',
    'timeout': 'Network requests can be slow — increase TIMEOUT if hitting limits',
    'not found': 'Check the URL is reachable and includes https://',
}

# Default HTTP request timeout in seconds.
_TIMEOUT_DEFAULT = 30


def validate(parsed_op):
    """Check METHOD, URL, and MODE are valid. Returns list of error strings."""
    errors = []

    url = (parsed_op.target or '').strip()
    if not url:
        errors.append('URL requires a target URL')
    elif not (url.startswith('http://') or url.startswith('https://')):
        errors.append('URL target must start with http:// or https://')

    mode = (parsed_op.directives.get('MODE') or 'fetch').strip().lower()
    if mode not in ('fetch', 'probe', 'download', 'json'):
        errors.append('MODE must be one of: fetch, probe, download, json')

    if mode == 'download' and not (parsed_op.directives.get('DEST') or '').strip():
        errors.append('download mode requires DEST directive')

    return errors


def _parse_headers(raw):
    """Parse HEADER directives into a dict of name: value pairs."""
    headers = {}
    if not raw:
        return headers
    for line in raw.strip().splitlines():
        line = line.strip()
        if '=' in line:
            k, _, v = line.partition('=')
            headers[k.strip()] = v.strip()
    return headers


def _strip_plain(html):
    """Strip HTML tags from text, returning plain readable content."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#39;', "'")
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _strip_markdown(html):
    """Convert HTML to markdown-style text, preserving links and structure."""
    for tag in ('script', 'style', 'nav', 'header', 'footer', 'aside', 'form'):
        html = re.sub(r'<%s[^>]*>.*?</%s>' % (tag, tag), '', html,
                      flags=re.DOTALL | re.IGNORECASE)

    lines = []

    for m in re.finditer(r'<h([1-3])[^>]*>(.*?)</h\1>', html,
                         flags=re.DOTALL | re.IGNORECASE):
        level = int(m.group(1))
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if text:
            lines.append('#' * level + ' ' + text)

    for m in re.finditer(r'<p[^>]*>(.*?)</p>', html,
                         flags=re.DOTALL | re.IGNORECASE):
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if text:
            lines.append(text)

    for m in re.finditer(r'<li[^>]*>(.*?)</li>', html,
                         flags=re.DOTALL | re.IGNORECASE):
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if text:
            lines.append('- ' + text)

    result = '\n\n'.join(lines) if lines else _strip_plain(html)
    result = result.replace('&amp;', '&').replace('&lt;', '<') \
                   .replace('&gt;', '>').replace('&nbsp;', ' ') \
                   .replace('&quot;', '"').replace('&#39;', "'")
    return result.strip()


def _jpath_get(obj, path):
    """Extract a value from a parsed JSON object using a dot-separated path."""
    parts = path.split('.')
    for part in parts:
        if isinstance(obj, dict):
            obj = obj[part]
        elif isinstance(obj, list):
            obj = obj[int(part)]
        else:
            raise KeyError(part)
    return obj


def _build_request(url, method, headers):
    """Build urllib Request object with headers and optional body."""
    req = urllib.request.Request(url, method=method)
    req.add_header('User-Agent', 'Forge-URL-Op/1.0')
    for k, v in headers.items():
        req.add_header(k, v)
    return req


def _do_fetch(url, headers, timeout, follow_redirects, strip_mode, capture):
    """Fetch URL and return response body as text, optionally stripped."""
    try:
        req = _build_request(url, 'GET', headers)
        opener = urllib.request.build_opener() if follow_redirects \
            else urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            capture['status_code'] = resp.status
            capture['content_type'] = resp.headers.get('Content-Type', '')
            capture['final_url'] = resp.url
            raw = resp.read().decode('utf-8', errors='replace')
        if strip_mode == 'no':
            capture['stdout'] = raw
        elif strip_mode == 'plain':
            capture['stdout'] = _strip_plain(raw)
        else:
            capture['stdout'] = _strip_markdown(raw)
    except urllib.error.HTTPError as e:
        capture['error'] = 'HTTP %s: %s' % (e.code, e.reason)
        capture['status_code'] = e.code
    except Exception as e:
        capture['error'] = str(e)


def _do_probe(url, headers, timeout, follow_redirects, capture):
    """HEAD request a URL and return status, headers, and redirect info."""
    redirect_chain = []

    class RedirectRecorder(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            redirect_chain.append((code, newurl))
            return super().redirect_request(req, fp, code, msg, hdrs, newurl)

    try:
        req = _build_request(url, 'HEAD', headers)
        opener = urllib.request.build_opener(RedirectRecorder())
        with opener.open(req, timeout=timeout) as resp:
            capture['status_code'] = resp.status
            capture['content_type'] = resp.headers.get('Content-Type', '')
            capture['content_length'] = resp.headers.get('Content-Length', 'unknown')
            capture['server'] = resp.headers.get('Server', 'unknown')
            capture['final_url'] = resp.url
            capture['redirect_chain'] = redirect_chain
        lines = [
            'Status:         %s' % capture['status_code'],
            'Content-Type:   %s' % capture['content_type'],
            'Content-Length: %s' % capture['content_length'],
            'Server:         %s' % capture['server'],
            'Final URL:      %s' % capture['final_url'],
        ]
        if redirect_chain:
            lines.append('Redirects:')
            for code, loc in redirect_chain:
                lines.append('  %s -> %s' % (code, loc))
        capture['stdout'] = '\n'.join(lines)
    except urllib.error.HTTPError as e:
        capture['error'] = 'HTTP %s: %s' % (e.code, e.reason)
        capture['status_code'] = e.code
    except Exception as e:
        capture['error'] = str(e)


def _do_download(url, headers, timeout, follow_redirects, dest_abs, capture):
    """Download URL to a file path under project root."""
    try:
        req = _build_request(url, 'GET', headers)
        opener = urllib.request.build_opener() if follow_redirects \
            else urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            capture['status_code'] = resp.status
            capture['content_type'] = resp.headers.get('Content-Type', '')
            capture['final_url'] = resp.url
            data = resp.read()
        os.makedirs(os.path.dirname(dest_abs) or '.', exist_ok=True)
        with open(dest_abs, 'wb') as f:
            f.write(data)
        size = len(data)
        capture['size'] = size
        capture['stdout'] = 'Downloaded %d bytes -> %s' % (size, dest_abs)
    except urllib.error.HTTPError as e:
        capture['error'] = 'HTTP %s: %s' % (e.code, e.reason)
        capture['status_code'] = e.code
    except Exception as e:
        capture['error'] = str(e)


def _do_json(url, headers, timeout, follow_redirects, jpath, capture):
    """Fetch URL, parse JSON response, optionally extract via JPATH."""
    try:
        req = _build_request(url, 'GET', headers)
        opener = urllib.request.build_opener() if follow_redirects \
            else urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            capture['status_code'] = resp.status
            capture['content_type'] = resp.headers.get('Content-Type', '')
            capture['final_url'] = resp.url
            raw = resp.read().decode('utf-8', errors='replace')
        parsed = json.loads(raw)
        if jpath:
            try:
                value = _jpath_get(parsed, jpath)
                capture['stdout'] = str(value) if not isinstance(value, (dict, list)) \
                    else json.dumps(value, indent=2)
            except (KeyError, IndexError, ValueError) as e:
                capture['error'] = 'JPATH "%s" not found: %s' % (jpath, e)
                return
        else:
            capture['stdout'] = json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        capture['error'] = 'JSON parse error: %s' % e
    except urllib.error.HTTPError as e:
        capture['error'] = 'HTTP %s: %s' % (e.code, e.reason)
        capture['status_code'] = e.code
    except Exception as e:
        capture['error'] = str(e)


def _do_post(url, method, headers, body_data, content_type, timeout, follow_redirects, capture):
    """Send POST/PUT/PATCH/DELETE request with optional JSON body."""
    try:
        data = body_data.encode('utf-8') if body_data else None
        req = _build_request(url, method.upper(), headers)
        req.add_header('Content-Type', content_type or 'application/json')
        opener = urllib.request.build_opener() if follow_redirects \
            else urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, data=data, timeout=timeout) as resp:
            capture['status_code'] = resp.status
            capture['content_type'] = resp.headers.get('Content-Type', '')
            capture['final_url'] = resp.url
            raw = resp.read().decode('utf-8', errors='replace')
        capture['stdout'] = raw.strip()
    except urllib.error.HTTPError as e:
        capture['error'] = 'HTTP %s: %s' % (e.code, e.reason)
        capture['status_code'] = e.code
        try:
            capture['stdout'] = e.read().decode('utf-8', errors='replace')
        except Exception:
            pass
    except Exception as e:
        capture['error'] = str(e)

def execute(ctx, parsed_op, result):
    """Dispatch URL op to the appropriate mode handler based on MODE directive."""
    url = parsed_op.target.strip()
    directives = parsed_op.directives

    mode = (directives.get('MODE') or 'fetch').strip().lower()
    method = (directives.get('METHOD') or '').strip().upper()
    strip_mode = (directives.get('STRIP') or 'markdown').strip().lower()
    dest_rel = (directives.get('DEST') or '').strip()
    raw_headers = directives.get('HEADERS') or ''
    timeout = int(directives.get('TIMEOUT') or _TIMEOUT_DEFAULT)
    follow = (directives.get('FOLLOW_REDIRECTS') or 'yes').strip().lower() != 'no'
    jpath = (directives.get('JPATH') or '').strip()
    body_data = (directives.get('BODY_DATA') or '').strip()
    content_type = (directives.get('CONTENT_TYPE') or 'application/json').strip()

    write_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}
    if not method:
        method = 'GET'

    headers = _parse_headers(raw_headers)
    capture = {'status_code': None, 'content_type': '', 'final_url': url,
               'stdout': '', 'error': None}

    if method in write_methods:
        target_fn = lambda: _do_post(url, method, headers, body_data,
                                     content_type, timeout, follow, capture)
    elif mode == 'download':
        dest_abs = os.path.join(ctx.project_root, dest_rel)
        target_fn = lambda: _do_download(url, headers, timeout, follow, dest_abs, capture)
    elif mode == 'probe':
        target_fn = lambda: _do_probe(url, headers, timeout, follow, capture)
    elif mode == 'json':
        target_fn = lambda: _do_json(url, headers, timeout, follow, jpath, capture)
    else:
        target_fn = lambda: _do_fetch(url, headers, timeout, follow, strip_mode, capture)

    t = threading.Thread(target=target_fn)
    t.daemon = True
    t.start()
    t.join(timeout + 2)

    if t.is_alive():
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'timeout after %ss' % timeout
        result['preview'] = 'URL %s [timeout]' % url
        return

    if capture.get('error') and not capture.get('stdout'):
        result['status'] = 'FAILED_IO'
        result['message'] = capture['error']
        result['preview'] = 'URL %s\nError: %s' % (url, capture['error'])
        return

    stdout = (capture.get('stdout') or '').strip()
    status_code = capture.get('status_code')

    result['status'] = 'APPLIED'
    result['message'] = '%s %s %s' % (method, mode, status_code or 'ok')
    result['stdout'] = stdout
    result['preview'] = _format_preview(url, mode, status_code, stdout)
    result['out'] = {
        'stdout': stdout,
        'lines': [l for l in stdout.splitlines() if l.strip()],
        'status_code': status_code,
        'content_type': capture.get('content_type', ''),
        'url': capture.get('final_url', url),
        'size': capture.get('size'),
        'dest': dest_rel or None,
        'redirect_chain': capture.get('redirect_chain', []),
    }

def _format_preview(url, mode, status_code, stdout):
    """Format response content into a compact preview string for the run packet."""
    lines = ['URL %s [%s %s]' % (url, mode, status_code or 'ok')]
    if stdout:
        content_lines = stdout.splitlines()
        if len(content_lines) > 80:
            lines += content_lines[:80]
            lines.append('... [%d more lines]' % (len(content_lines) - 80))
        else:
            lines += content_lines
    return '\n'.join(lines).rstrip() + '\n'
