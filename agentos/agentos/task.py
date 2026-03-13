"""
Task abstraction for AgentOS.

A `Task` encapsulates a unit of work.  It stores a callable along with the
arguments needed to execute it.  When executed, the task simply calls the
underlying function and returns its result.  Tasks may be run synchronously
via :meth:`run` or awaited asynchronously when used through an `Agent`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional, Tuple


@dataclass
class Task:
    """Represents a unit of work consisting of a callable and arguments.

    Parameters
    ----------
    description: str
        A human‑readable description of what this task does.  Used for
        logging or debugging.
    func: Callable[..., Any]
        The function or callable to execute.
    args: Tuple[Any, ...], optional
        Positional arguments to pass to the callable when run.
    kwargs: Dict[str, Any], optional
        Keyword arguments to pass to the callable when run.

    Notes
    -----
    Tasks are lightweight wrappers around callables.  They do not store
    state beyond the function and its arguments.  If you need to maintain
    state across multiple tasks, consider storing that state on the agent
    itself or in an external object.
    """

    description: str
    func: Callable[..., Any]
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def run(self) -> Any:
        """Execute the underlying callable and return its result.

        Returns
        -------
        Any
            The return value of the underlying function.
        """
        return self.func(*self.args, **self.kwargs)

    def __call__(self) -> Any:
        """Delegate to :meth:`run` so that a `Task` can be called like a function."""
        return self.run()

    def __repr__(self) -> str:
        return f"Task(description={self.description!r}, func={self.func.__name__}, args={self.args}, kwargs={self.kwargs})"
