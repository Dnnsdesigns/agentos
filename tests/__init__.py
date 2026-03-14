"""Test package for AgentOS.

This module initializes the test suite and provides common test utilities
for all AgentOS components.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

__version__ = "0.1.0"
__author__ = "AgentOS Contributors"

# Import test modules for easier access
from tests.test_agent import TestAgent
from tests.test_task import TestTask
from tests.test_spec import TestSpec

__all__ = [
    "TestAgent",
    "TestTask",
    "TestSpec",
]