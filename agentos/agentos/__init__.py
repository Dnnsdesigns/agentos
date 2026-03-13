"""
AgentOS core package.

This package provides a simple framework for managing AI agents and tasks.
It exposes high‑level classes and functions to help organise your agentic
projects.  The most important abstractions are:

* :class:`agentos.agent.Agent` – represents a single agent with a name,
  description and a task queue.
* :class:`agentos.task.Task` – encapsulates a unit of work to be executed.
* :class:`agentos.manager.AgentManager` – coordinates multiple agents and
  schedules tasks across them.
* :func:`agentos.standards.discover_standards` – scan a codebase for coding
  conventions.
* :func:`agentos.standards.inject_standards` – inject standards into text
  such as a specification.
* :class:`agentos.spec.Spec` – a simple specification model used for
  organising product or feature descriptions.

The package defines a `__version__` attribute which can be useful for
logging or debugging.

Usage example:

>>> from agentos.agent import Agent
>>> from agentos.task import Task
>>> def greet(name):
...     return f"Hello, {name}!"
>>> agent = Agent(name="Greeter", description="Says hello")
>>> agent.add_task(Task(description="Say hi", func=greet, args=("World",)))
>>> results = agent.run_tasks()
>>> print(results[0])
Hello, World!

This simple example shows how to construct an agent, add a task, and run it.
See the `README.md` for a more complete overview.
"""

from importlib import metadata


__all__ = [
    "agent",
    "task",
    "manager",
    "standards",
    "spec",
    "utils",
]

# Expose top‑level classes for convenience
from .agent import Agent  # noqa: F401
from .task import Task  # noqa: F401
from .manager import AgentManager  # noqa: F401
from .spec import Spec  # noqa: F401
from .standards import discover_standards, inject_standards  # noqa: F401


def _get_version() -> str:
    """Return the package version from package metadata.

    If the package is installed via pip, this will return the version
    specified in `pyproject.toml` or `setup.py`.  When running from a
    development checkout without packaging metadata, a default version
    of "0.0.0" will be returned.
    """
    try:
        return metadata.version(__name__)
    except metadata.PackageNotFoundError:
        return "0.0.0"


__version__ = _get_version()
