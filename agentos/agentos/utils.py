"""
Utility functions for AgentOS.

This module collects miscellaneous helper functions used throughout the
AgentOS framework.  These helpers are intentionally general and have
minimal dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List


def list_python_files(path: str | Path) -> List[str]:
    """Return a list of Python source files under a directory.

    Parameters
    ----------
    path: str or Path
        The directory to search.

    Returns
    -------
    list of str
        Paths to `.py` files found recursively.
    """
    p = Path(path)
    return [str(file) for file in p.rglob("*.py")]
