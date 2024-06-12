# Copyright (c) 2023-2024, zhaowcheng <zhaowcheng@163.com>

"""
Utility functions.
"""

import re
import string


def remove_ansi_escape_chars(s: str) -> str:
    """
    Remove ansi esacpe characters from `s`.

    >>> remove_ansi_escape_chars('\x1b[31mhello\x1b[0m')
    'hello'
    """
    escapes = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return escapes.sub('', s)


def remove_unprintable_chars(s: str) -> str:
    """
    Remove unprintable characters from `s`.

    >>> remove_unprintable_chars('hello\xe9')
    'hello'
    """
    return ''.join(c for c in s if c in string.printable)

