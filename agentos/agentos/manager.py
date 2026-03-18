"""
Agent manager and scheduling utilities.

The :class:`AgentManager` coordinates the execution of multiple agents
concurrently.  It maintains a registry of agents, schedules their tasks,
and provides mechanisms for asynchronous execution.  The manager also
exposes utility functions related to the high‑level architecture described in
the Agent‑OS whitepapers, such as unified memory management and zero‑copy
object registration.  While the hardware‑specific details of the A‑1
processor are beyond the scope of this pure Python module, the concepts
are represented here to illustrate how such a system might be orchestrated
from user space.

This module demonstrates:

* Managing multiple agents and delegating tasks between them.
* A simple work queue with priorities.
* An in‑process simulation of zero‑copy object registration using
  memory‑mapped files and Python’s mmap module.
* A stubbed out representation of an asynchronous task graph similar to
  what might be submitted to the A‑1 Cognitive Processor.

For a production system targeting the actual A‑1 hardware, these classes
would need to interface with the kernel driver described in the system
architecture, using `ioctl` calls and memory pinning to register data
structures with the NPU.
"""

from __future__ import annotations

import asyncio
import heapq
import mmap
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .agent import Agent
from .task import Task


class AgentManager:
    """Coordinates multiple agents and schedules their tasks.

    The manager keeps a registry of agents indexed by name and manages a
    priority queue of tasks.  It supports running tasks either in a
    dedicated worker thread or using asynchronous coroutines.

    Parameters
    ----------
    use_async: bool, optional
        If true, tasks will be scheduled using asyncio; otherwise they
        will run in a background thread.  Defaults to False.

    Notes
    -----
    The scheduler provided here is intentionally simple.  It executes tasks
    in order of their assigned priority (lower numbers are higher priority).
    More sophisticated priority scheduling and dependency resolution can
    build upon these foundations.
    """

    def __init__(self, use_async: bool = False) -> None:
        self.agents: Dict[str, Agent] = {}
        self._task_queue: List[Tuple[int, int, Task]] = []  # (priority, counter, task)
        self._counter: int = 0
        self.use_async: bool = use_async
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        if not use_async:
            self._start_worker()

    def _start_worker(self) -> None:
        """Start a background thread to process tasks when not using asyncio."""

        def worker() -> None:
            while not self._stop_event.is_set():
                task_entry = None
                with self._lock:
                    if self._task_queue:
                        task_entry = heapq.heappop(self._task_queue)
                if task_entry:
                    _, _, task = task_entry
                    try:
                        task.run()
                    except Exception:
                        # In a real system, we would log or propagate this exception.
                        pass
                else:
                    # Sleep briefly to prevent busy waiting.
                    self._stop_event.wait(0.01)

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the manager.

        Parameters
        ----------
        agent: Agent
            The agent instance to register.  If an agent with the same
            name already exists, it will be replaced.
        """
        self.agents[agent.name] = agent

    def schedule_task(self, task: Task, priority: int = 0) -> None:
        """Schedule a task for execution.

        Parameters
        ----------
        task: Task
            The task to schedule.
        priority: int, optional
            Lower values indicate higher priority.  Defaults to 0.
        """
        with self._lock:
            heapq.heappush(self._task_queue, (priority, self._counter, task))
            self._counter += 1

    async def schedule_task_async(self, task: Task, priority: int = 0) -> None:
        """Asynchronously schedule a task for execution.

        This method can be used when the manager is configured for
        asynchronous operation.  It adds the task to the priority queue
        and immediately returns.
        """

        # Acquire lock synchronously because heapq is not thread safe.
        def sync_push() -> None:
            with self._lock:
                heapq.heappush(self._task_queue, (priority, self._counter, task))
                self._counter += 1

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sync_push)

    def stop(self) -> None:
        """Signal the manager to stop its worker thread and flush tasks."""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join()

    # -------------------------------------------------------------------------
    # Unified memory management (conceptual)
    # -------------------------------------------------------------------------

    def mmap_file(self, path: str) -> mmap.mmap:
        """Memory‑map a file and return an mmap object.

        This method wraps Python’s built‑in mmap facility to map the
        contents of a file into memory.  The memory map can then be passed
        around by reference without copying, reflecting the zero‑copy design
        described in the Agent‑OS architecture.  The returned mmap object
        should be closed by the caller when no longer needed.

        Parameters
        ----------
        path: str
            Path to the file to memory‑map.

        Returns
        -------
        mmap.mmap
            A memory‑mapped view of the file’s contents.
        """
        file_size = os.path.getsize(path)
        fd = os.open(path, os.O_RDONLY)
        try:
            return mmap.mmap(fd, file_size, access=mmap.ACCESS_READ)
        finally:
            os.close(fd)

    @dataclass
    class RegisteredObject:
        """Represents an object registered for zero‑copy access.

        This class serves as a placeholder for the concept of I/O Virtual
        Addresses (IOVAs).  In the real Agent‑OS implementation, the
        kernel driver would return a stable IOVA for the registered memory
        region.  Here, we simply use the Python `id` of the mmap object as
        a stand‑in to demonstrate the API shape.
        """

        handle: Any
        iova: int
        length: int

    def register_object(self, mm: mmap.mmap) -> RegisteredObject:
        """Register a memory‑mapped object for zero‑copy operations.

        In a real system this would call into a driver via ioctl to pin
        the pages and assign an IOVA.  Here we simulate by using Python’s
        `id` function to derive a unique number representing the memory.

        Parameters
        ----------
        mm: mmap.mmap
            The memory‑mapped region to register.

        Returns
        -------
        RegisteredObject
            A descriptor containing a simulated IOVA and the length of the
            mapped region.
        """
        return AgentManager.RegisteredObject(handle=mm, iova=id(mm), length=len(mm))

    # -------------------------------------------------------------------------
    # Task graph representation (conceptual)
    # -------------------------------------------------------------------------

    @dataclass
    class TaskNode:
        """Represents a node in a task graph submitted to hardware.

        This dataclass mirrors the conceptual A1_TaskNode descriptor
        described in the architecture documents.  It holds the operation
        type, input/output references, and scheduling metadata.  It can be
        serialised into a byte structure for submission via `submit_graph`.

        Parameters
        ----------
        op: str
            Operation type (e.g., "TGEMM", "TATTN").
        inputs: List[int]
            List of IOVA addresses for input objects.
        outputs: List[int]
            List of IOVA addresses where output should be written.
        deps: List[int]
            List of dependency IDs.  A node will not execute until all
            dependencies are resolved.
        priority: int
            Scheduling priority; lower numbers are higher priority.
        tile_mask: int
            Bitmask indicating which NPU tiles are eligible to execute the node.
        """

        op: str
        inputs: List[int]
        outputs: List[int]
        deps: List[int] = field(default_factory=list)
        priority: int = 0
        tile_mask: int = 0

        def to_bytes(self) -> bytes:
            """Serialize the task node into bytes for submission.

            This method packs the fields into a simple delimited string for
            demonstration.  A real implementation would use `ctypes` or the
            struct module to match the binary layout expected by the driver.
            """
            parts = [self.op, str(self.priority), str(self.tile_mask)]
            parts += [",".join(str(i) for i in self.inputs)]
            parts += [",".join(str(o) for o in self.outputs)]
            parts += [",".join(str(d) for d in self.deps)]
            # Use pipe (|) as a delimiter between fields
            return "|".join(parts).encode("utf-8")

    def submit_graph(self, nodes: Iterable[TaskNode]) -> None:
        """Submit a task graph to the (simulated) hardware queue.

        This function simply iterates over the provided nodes and prints
        their serialized representation.  In a real system, this would
        write into a memory‑mapped command queue and ring a doorbell
        register on the A‑1 device.  The goal here is to illustrate how
        application code could transform high‑level operations into
        hardware consumable structures.

        Parameters
        ----------
        nodes: Iterable[AgentManager.TaskNode]
            An iterable of task nodes representing a workload graph.
        """
        for node in nodes:
            payload = node.to_bytes()
            # In a real implementation, write `payload` into the device’s
            # command queue and then ring the doorbell.  Here we log it.
            print(f"Submitting TaskNode: {payload.decode('utf-8')}")
