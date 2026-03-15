"""Test package for AgentOS.

This module initializes the test suite and provides common test utilities
for all AgentOS components.
"""

import sys
from pathlib import Path

# Add the directory containing the agentos package to sys.path so that
# ``from agentos.agent import Agent`` works when running tests directly.
_pkg_root = Path(__file__).parent.parent / "agentos"
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

__version__ = "0.1.0"
__author__ = "AgentOS Contributors"