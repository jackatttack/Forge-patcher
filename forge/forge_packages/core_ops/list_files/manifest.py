MANIFEST = {
    'name': 'list_files',
    'op': 'LIST_FILES',
    'kind': 'core-op',
    'version': '0.2.0',
    'required': True,
    'risk': 'read-only',
    'domains': ['filesystem', 'orientation', 'surface'],
    'provides_pages': ['files.tree.*'],
    'summary': 'List directory contents as an orientation tree with structured surface data.',
}
