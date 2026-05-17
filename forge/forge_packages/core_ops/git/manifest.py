# -*- coding: utf-8 -*-

MANIFEST = {
    'name': 'git',
    'op': 'GIT',
    'kind': 'core-op',
    'version': '0.1.0',
    'summary': 'Inspect and update the configured GitHub repo through the GitHub API.',
    'required': False,
    'risk': 'network-write',
    'domains': ['github', 'release', 'sync', 'upload', 'repository'],
    'status_codes': ['APPLIED', 'FAILED_PARSE', 'FAILED_RUNTIME', 'FAILED_NOT_FOUND'],
    'provides_pages': ['op.detail.N'],
}