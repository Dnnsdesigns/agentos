# Release Notes

This page documents all releases of AgentOS. For a compact summary see the [CHANGELOG](../CHANGELOG.md).

---

## v0.1.0 — 2026-04-06

**Initial release of AgentOS.**

This is the first public release of the framework. It establishes the core abstractions, tooling, and project structure that future releases will build upon.

### Highlights

| Area | What's new |
|------|-----------|
| Agent abstraction | `Agent` class with named task queues, synchronous and async execution |
| Task management | `Task` dataclass wrapping any callable with positional and keyword arguments |
| Agent coordination | `AgentManager` with a background worker thread and priority queue scheduling |
| Async support | Full `asyncio` execution path for coroutine-based tasks |
| Standards discovery | `discover_standards()` scans Python codebases for line-length, docstring coverage, and naming style metrics |
| Standards injection | `inject_standards()` appends discovered standards to markdown specifications |
| Specification model | `Spec` dataclass with markdown rendering and standards integration |
| CLI | `agentos discover`, `agentos spec`, and `agentos inject` subcommands |
| Type safety | Full type annotations; strict mypy compliance (Python 3.10 target) |
| Tests | Initial test suite covering all core modules |
| Packaging | `pyproject.toml`-based build with `setuptools`; `py.typed` marker for PEP 561 |

### Added

- **`Agent`** – Represents an autonomous agent. Maintains an ordered task queue. Supports `add_task()` with either a `Task` instance or a raw callable. `run_tasks()` executes synchronously; `run_tasks_async()` uses `asyncio` (running sync callables in the default executor to avoid blocking the event loop).
- **`Task`** – Lightweight dataclass (`description`, `func`, `args`, `kwargs`). Can be called directly via `task()` or `task.run()`.
- **`AgentManager`** – Coordinates multiple registered agents and a shared priority task queue. In synchronous mode a daemon worker thread continuously pops and executes tasks. In async mode tasks are enqueued via `schedule_task_async()`. Exposes `mmap_file()` / `register_object()` for zero-copy memory access concepts, and `submit_graph()` / `TaskNode` for task-graph submission to hardware accelerators.
- **`discover_standards(path)`** – Recursively scans `.py` files under `path`. Returns a dictionary with:
  - `max_line_length`
  - `average_line_length`
  - `functions_with_docstrings` (fraction 0–1)
  - `variable_naming_style` (`snake_case`, `camelCase`, or `undetermined`)
  - `files_scanned`
- **`inject_standards(spec_text, standards)`** – Appends or replaces a `## Coding Standards` section in a markdown document.
- **`Spec`** – Dataclass with `title`, `description`, and `items`. Methods: `add_item()`, `to_markdown()`, `to_dict()`, `from_dict()`. `to_markdown(include_standards=...)` will call `inject_standards` automatically.
- **CLI** (`agentos` / `python -m agentos`):
  - `discover` – scan a directory and write or print standards JSON.
  - `spec` – create a specification markdown document.
  - `inject` – inject standards into an existing specification file.
- **`pyproject.toml`** – Defines build system, project metadata, dependencies (none), scripts, and tool configurations for Black, isort, and mypy.
- **`py.typed`** marker – PEP 561 compliance; downstream consumers can type-check against AgentOS.
- **GitHub Actions CI** – Automated lint, type-check, and test workflow on push and pull requests.
- **GitHub Actions release workflow** – Automated build and PyPI publication on version tag push.

### Changed

N/A — initial release.

### Fixed

N/A — initial release.

### Known Limitations

- `AgentManager` does not yet support distributed execution across processes or machines.
- `discover_standards` only analyses Python files; support for other languages is planned.
- No built-in retry or error-handling policy for failed tasks; exceptions are currently silently swallowed in the worker thread.

---

## Upcoming

The following improvements are being considered for future releases:

- Task retry policies and error callbacks
- Dependency graphs between tasks (DAG scheduling)
- Plugin system for custom agent behaviours
- Cross-language standards discovery
- Distributed agent coordination via message queues

To follow development or contribute ideas, see the [GitHub Issues](https://github.com/Dnnsdesigns/agentos/issues) page.
