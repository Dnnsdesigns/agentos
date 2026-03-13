"""
Definition of the `Agent` class.

An Agent is the fundamental unit of execution in AgentOS.  It maintains a
queue of tasks and executes them in order when requested.  Each agent has a
name and optional description to help distinguish it from others in the
system.  This module defines the class and its associated methods.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, List, Optional, Tuple

from .task import Task


class Agent:
    """Represents an autonomous agent with a queue of tasks.

    Parameters
    ----------
    name: str
        A human‑readable name identifying the agent.
    description: str, optional
        A longer description of the agent’s purpose or capabilities.

    Attributes
    ----------
    name: str
        The name of the agent.
    description: Optional[str]
        Human‑readable description of the agent.
    _tasks: List[Task]
        Internal list of tasks queued for execution.

    Notes
    -----
    Tasks are executed in the order they are added.  Use
    :meth:`add_task` to append a new task.  To run the tasks
    asynchronously, call :meth:`run_tasks_async` instead of
    :meth:`run_tasks`.
    """

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        self.name: str = name
        self.description: Optional[str] = description
        self._tasks: List[Task] = []

    def add_task(
        self, task: Task | Callable[..., Any], *args: Any, description: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Add a new task to the agent’s queue.

        A task can be provided either as a pre‑constructed :class:`Task`
        instance or as a callable.  If a callable is given, it will be
        wrapped in a `Task` with the provided positional and keyword
        arguments.

        Parameters
        ----------
        task: Task or Callable[..., Any]
            The task object or function to run.
        *args: Any
            Positional arguments to pass to the function when wrapping a
            callable.
        description: str, optional
            A description of what the task does.  Ignored if `task` is
            already a `Task` instance.
        **kwargs: Any
            Keyword arguments to pass to the function when wrapping a callable.
        """
        if isinstance(task, Task):
            self._tasks.append(task)
        else:
            self._tasks.append(Task(description=description or task.__name__, func=task, args=args, kwargs=kwargs))

    def run_tasks(self) -> List[Any]:
        """Run all tasks sequentially and return their results.

        Returns
        -------
        List[Any]
            A list of results from each task, in the order they were
            executed.
        """
        results: List[Any] = []
        for task in self._tasks:
            results.append(task.run())
        # Clear tasks once executed so they aren’t run again accidentally.
        self._tasks.clear()
        return results

    async def run_tasks_async(self) -> List[Any]:
        """Asynchronously run all tasks and return their results.

        Tasks are awaited one after another, which makes sense when the
        underlying callable is a coroutine.  If a task’s function is not
        asynchronous, it will be executed in the default executor.

        Returns
        -------
        List[Any]
            A list of results from each task.
        """
        results: List[Any] = []
        loop = asyncio.get_event_loop()
        for task in self._tasks:
            if asyncio.iscoroutinefunction(task.func):
                results.append(await task.func(*task.args, **task.kwargs))
            else:
                # Run sync function in executor to avoid blocking the event loop.
                results.append(await loop.run_in_executor(None, task.func, *task.args, **task.kwargs))
        self._tasks.clear()
        return results

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, description={self.description!r}, tasks={len(self._tasks)})"
