# -*- coding: utf-8 -*-
"""
result_models.py
================
Normalized execution-result helpers.
"""

def make_result(op_name, target):
    """Return a fresh result dict with default status fields for an op."""
    return {
        'op': op_name,
        'target': target,
        'status': 'UNKNOWN',
        'message': '',
        'preview': '',
        'file': '',
    }
