# -*- coding: utf-8 -*-

MANIFEST = {
    'name': 'pack',
    'op': 'PACK',
    'kind': 'core-op',
    'version': '0.1.0',
    'summary': 'Pack selected files into a portable self-installing Python script.',
    'required': False,
    'risk': 'file-write',
    'domains': ['release', 'packaging', 'installer', 'export'],
    'status_codes': ['APPLIED', 'FAILED_PARSE', 'FAILED_NOT_FOUND', 'FAILED_IO'],
}