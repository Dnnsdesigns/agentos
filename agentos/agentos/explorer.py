"""
Explorer agent for AgentOS.

This module defines :class:`ExplorerAgent`, a specialised :class:`Agent`
subclass that traverses directory trees to discover files and directories.
Callers can filter results by file extension or by a glob‑style pattern,
and can optionally queue a handler task for every discovered entry.

Typical usage::

    from agentos.explorer import ExplorerAgent

    agent = ExplorerAgent(name="Indexer", root_path="/my/project")

    # Collect all Python files
    py_files = agent.explore(extensions=[".py"])

    # Queue a task for each discovered file and then run them
    def analyse(info):
        print(f"Analysing {info.path}: {info.size} bytes")

    agent.queue_file_tasks(analyse, extensions=[".py"])
    agent.run_tasks()
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence

from .agent import Agent
from .task import Task


@dataclass
class FileInfo:
    """Metadata about a single filesystem entry discovered during exploration.

    Parameters
    ----------
    path: Path
        Absolute path to the entry.
    name: str
        The bare file or directory name (``path.name``).
    extension: str
        Lower‑cased file extension including the leading dot, or an empty
        string for directories and extension‑less files.
    size: int
        Size of the file in bytes.  Always ``0`` for directories.
    is_directory: bool
        ``True`` if this entry is a directory; ``False`` for regular files.
    """

    path: Path
    name: str
    extension: str
    size: int
    is_directory: bool

    def __str__(self) -> str:
        kind = "dir" if self.is_directory else "file"
        return f"FileInfo({kind}, path={self.path}, size={self.size})"


class ExplorerAgent(Agent):
    """An agent specialised for exploring directory trees.

    In addition to the task queue inherited from :class:`Agent`,
    ``ExplorerAgent`` exposes :meth:`explore` for collecting filesystem
    entries and :meth:`queue_file_tasks` for automatically queueing a
    handler task for each discovered entry.

    Parameters
    ----------
    name: str
        A human‑readable name for the agent.
    description: str, optional
        Longer description of the agent's purpose.
    root_path: str or Path, optional
        Default directory to use when no path is supplied to :meth:`explore`
        or :meth:`queue_file_tasks`.

    Attributes
    ----------
    root_path: Path or None
        The default exploration root.
    _last_results: List[FileInfo]
        Results from the most recent call to :meth:`explore`.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        root_path: Optional[str | Path] = None,
    ) -> None:
        super().__init__(name=name, description=description)
        self.root_path: Optional[Path] = Path(root_path) if root_path is not None else None
        self._last_results: List[FileInfo] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def explore(
        self,
        path: Optional[str | Path] = None,
        *,
        extensions: Optional[Sequence[str]] = None,
        pattern: Optional[str] = None,
        recursive: bool = True,
        include_dirs: bool = False,
    ) -> List[FileInfo]:
        """Walk a directory tree and return matching :class:`FileInfo` entries.

        Parameters
        ----------
        path: str or Path, optional
            Directory to start from.  Falls back to :attr:`root_path` when
            not provided.  Raises :class:`ValueError` if neither is set.
        extensions: sequence of str, optional
            Only return files whose extension (lower‑cased, including the
            leading dot, e.g. ``".py"``) appears in this list.  Ignored
            when *pattern* is given.
        pattern: str, optional
            A ``fnmatch``‑style pattern matched against the bare file name
            (e.g. ``"*.py"`` or ``"test_*"``).  Takes precedence over
            *extensions* when both are supplied.
        recursive: bool, optional
            If ``True`` (the default) the entire subtree is traversed.
            If ``False`` only the immediate children of *path* are
            considered.
        include_dirs: bool, optional
            When ``True``, directories that match the filter are included in
            the results alongside files.  Defaults to ``False``.

        Returns
        -------
        List[FileInfo]
            A list of matching filesystem entries sorted by path.

        Raises
        ------
        ValueError
            If *path* is not provided and :attr:`root_path` is ``None``.
        NotADirectoryError
            If the resolved *path* is not a directory.
        """
        root = self._resolve_path(path)
        results: List[FileInfo] = []

        if recursive:
            entries = self._walk_recursive(root)
        else:
            entries = self._walk_flat(root)

        for entry_path, is_dir in entries:
            if is_dir and not include_dirs:
                continue
            name = entry_path.name
            if not self._matches(name, is_dir, extensions=extensions, pattern=pattern):
                continue
            ext = "" if is_dir else entry_path.suffix.lower()
            size = 0 if is_dir else self._safe_size(entry_path)
            results.append(
                FileInfo(
                    path=entry_path,
                    name=name,
                    extension=ext,
                    size=size,
                    is_directory=is_dir,
                )
            )

        results.sort(key=lambda fi: fi.path)
        self._last_results = results
        return results

    def queue_file_tasks(
        self,
        handler: Callable[[FileInfo], Any],
        path: Optional[str | Path] = None,
        *,
        extensions: Optional[Sequence[str]] = None,
        pattern: Optional[str] = None,
        recursive: bool = True,
        include_dirs: bool = False,
        task_description_prefix: str = "explore",
    ) -> List[FileInfo]:
        """Explore a directory and queue a handler task for each match.

        This is a convenience method that calls :meth:`explore` and then
        wraps each discovered :class:`FileInfo` in a :class:`Task` that
        invokes *handler*.  The tasks are added to the agent's queue and
        can be run via :meth:`run_tasks` or :meth:`run_tasks_async`.

        Parameters
        ----------
        handler: Callable[[FileInfo], Any]
            A callable that accepts a single :class:`FileInfo` argument.
        path: str or Path, optional
            Root directory to explore.  Defaults to :attr:`root_path`.
        extensions: sequence of str, optional
            Forwarded to :meth:`explore`.
        pattern: str, optional
            Forwarded to :meth:`explore`.
        recursive: bool, optional
            Forwarded to :meth:`explore`.
        include_dirs: bool, optional
            Forwarded to :meth:`explore`.
        task_description_prefix: str, optional
            Prefix used when building task descriptions.

        Returns
        -------
        List[FileInfo]
            The list of discovered entries, one task queued per entry.
        """
        found = self.explore(
            path,
            extensions=extensions,
            pattern=pattern,
            recursive=recursive,
            include_dirs=include_dirs,
        )
        for info in found:
            self.add_task(
                Task(
                    description=f"{task_description_prefix}: {info.path}",
                    func=handler,
                    args=(info,),
                )
            )
        return found

    @property
    def last_results(self) -> List[FileInfo]:
        """Return results from the most recent :meth:`explore` call."""
        return list(self._last_results)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_path(self, path: Optional[str | Path]) -> Path:
        """Return a validated Path, falling back to :attr:`root_path`."""
        if path is not None:
            resolved = Path(path)
        elif self.root_path is not None:
            resolved = self.root_path
        else:
            raise ValueError(
                "No path provided and ExplorerAgent.root_path is not set."
            )
        if not resolved.is_dir():
            raise NotADirectoryError(f"{resolved!r} is not a directory.")
        return resolved

    @staticmethod
    def _walk_recursive(root: Path) -> List[tuple[Path, bool]]:
        """Return all entries under *root* recursively."""
        entries: List[tuple[Path, bool]] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dp = Path(dirpath)
            for dn in dirnames:
                entries.append((dp / dn, True))
            for fn in filenames:
                entries.append((dp / fn, False))
        return entries

    @staticmethod
    def _walk_flat(root: Path) -> List[tuple[Path, bool]]:
        """Return immediate children of *root* only."""
        entries: List[tuple[Path, bool]] = []
        for child in root.iterdir():
            entries.append((child, child.is_dir()))
        return entries

    @staticmethod
    def _matches(
        name: str,
        is_dir: bool,
        *,
        extensions: Optional[Sequence[str]],
        pattern: Optional[str],
    ) -> bool:
        """Return ``True`` if an entry satisfies the active filter."""
        if pattern is not None:
            return fnmatch.fnmatch(name, pattern)
        if extensions is not None and not is_dir:
            suffix = Path(name).suffix.lower()
            return suffix in extensions
        # No filter active; include everything.
        return True

    @staticmethod
    def _safe_size(path: Path) -> int:
        """Return file size in bytes, or 0 if the stat call fails."""
        try:
            return path.stat().st_size
        except OSError:
            return 0

    def __repr__(self) -> str:
        return (
            f"ExplorerAgent(name={self.name!r}, "
            f"root_path={self.root_path!r}, "
            f"tasks={len(self._tasks)})"
        )
