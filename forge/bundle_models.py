# -*- coding: utf-8 -*-
"""
bundle_models.py
================
Normalized structures for parser output.

Simple and boring on purpose.
"""

try:
    from dataclasses import dataclass, field
except Exception:
    dataclass = None
    field = None


if dataclass is not None:

    @dataclass
    class ParsedOp(object):
        op: str
        target: str
        directives: dict
        body: str = ''
        default_file: str = None

    @dataclass
    class ParseResult(object):
        ops: list
        default_file: str = None
        errors: list = field(default_factory=list)

else:

    class ParsedOp(object):
        def __init__(self, op, target, directives=None, body='', default_file=None):
            self.op = op
            self.target = target
            self.directives = directives or {}
            self.body = body
            self.default_file = default_file

    class ParseResult(object):
        def __init__(self, ops=None, default_file=None, errors=None):
            self.ops = ops or []
            self.default_file = default_file
            self.errors = errors or []
