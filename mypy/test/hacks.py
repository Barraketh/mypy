"""This file exists as a temporary measure, and will be removed when new
semantic analyzer is the default one.
"""
MYPY = False
if MYPY:
    from typing_extensions import Final

# Files to not run with new semantic analyzer.
new_semanal_blacklist = [
    'check-incremental.test',
]  # type: Final
