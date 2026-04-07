# AgentOS Wiki

Welcome to the **AgentOS** wiki. AgentOS is a lightweight, extensible Python framework for building and managing autonomous AI agents. This page provides an overview of the project, installation instructions, core concepts, CLI usage, and guidance for contributors.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [Agent](#agent)
  - [Task](#task)
  - [AgentManager](#agentmanager)
  - [Standards Discovery](#standards-discovery)
  - [Specification Shaping](#specification-shaping)
- [CLI Reference](#cli-reference)
- [Project Layout](#project-layout)
- [Contributing](#contributing)
- [Release Notes](#release-notes)
- [License](#license)

---

## Overview

AgentOS provides a simple but extensible foundation for creating agentic systems. It abstracts common concerns—such as task scheduling, standards discovery, and specification shaping—into reusable components that work with any underlying model or tooling.

Key design principles:

- **No external dependencies** – the core package has zero runtime dependencies.
- **Plain Python classes** – all objects are standard Python dataclasses or classes with clear interfaces, making them easy to extend or swap out.
- **Async-first** – execution supports both synchronous and `asyncio`-based asynchronous modes.
- **Model-agnostic** – not tied to any particular AI provider.

---

## Installation

### Requirements

- Python 3.8 or higher

### From source (development)

```bash
git clone https://github.com/Dnnsdesigns/agentos.git
cd agentos
pip install -e .
```

### Development dependencies

```bash
pip install black isort mypy pytest
```

---

## Quick Start

```python
from agentos import Agent, Task, AgentManager

# Define some work
def fetch_data(url: str) -> str:
    return f"data from {url}"

# Create an agent
agent = Agent(name="DataAgent", description="Fetches data from URLs")

# Add a task to the agent
agent.add_task(fetch_data, "https://example.com", description="Fetch example.com")

# Run the agent's tasks directly
results = agent.run_tasks()
print(results)  # ['data from https://example.com']

# Or coordinate multiple agents with a manager
manager = AgentManager()
manager.register_agent(agent)

task = Task(description="another task", func=fetch_data, args=("https://other.com",))
manager.schedule_task(task, priority=1)
manager.stop()
```

---

## Core Concepts

### Agent

`agentos.Agent` is the fundamental unit of execution. Each agent:

- Has a **name** and optional **description**.
- Maintains an internal **task queue** (`List[Task]`).
- Provides `add_task()` to enqueue work.
- Provides `run_tasks()` (synchronous) and `run_tasks_async()` (async) to execute queued work.

```python
from agentos import Agent, Task

agent = Agent(name="MyAgent", description="Example agent")

# Add a pre-built Task
task = Task(description="Say hello", func=print, args=("Hello!",))
agent.add_task(task)

# Or add a callable directly
agent.add_task(print, "World!", description="Print world")

results = agent.run_tasks()
```

After `run_tasks()` or `run_tasks_async()` completes, the task queue is **cleared** so tasks are not accidentally re-run.

**Async execution**:

```python
import asyncio

async def my_coroutine():
    return 42

agent = Agent(name="AsyncAgent")
agent.add_task(my_coroutine)
results = asyncio.run(agent.run_tasks_async())
print(results)  # [42]
```

---

### Task

`agentos.Task` is a lightweight dataclass encapsulating a callable and its arguments.

| Field         | Type                  | Description                              |
|---------------|-----------------------|------------------------------------------|
| `description` | `str`                 | Human-readable label used for debugging  |
| `func`        | `Callable[..., Any]`  | The function or coroutine to execute     |
| `args`        | `Tuple[Any, ...]`     | Positional arguments (default: `()`)     |
| `kwargs`      | `Dict[str, Any]`      | Keyword arguments (default: `{}`)        |

```python
from agentos import Task

def add(a: int, b: int) -> int:
    return a + b

task = Task(description="add 1+2", func=add, args=(1, 2))
print(task.run())  # 3
print(task())      # 3  (Task is also callable)
```

---

### AgentManager

`agentos.AgentManager` coordinates multiple agents, maintains a **priority queue** of tasks, and manages a background worker thread (or async loop).

```python
from agentos import AgentManager, Task

manager = AgentManager()  # starts a background worker thread

task = Task(description="low priority", func=print, args=("low",))
urgent_task = Task(description="high priority", func=print, args=("high!",))

manager.schedule_task(task, priority=10)
manager.schedule_task(urgent_task, priority=0)  # lower number = higher priority

manager.stop()  # flush remaining tasks and join the worker thread
```

**Async mode**:

```python
import asyncio
from agentos import AgentManager, Task

async def main():
    manager = AgentManager(use_async=True)
    task = Task(description="async task", func=print, args=("hello",))
    await manager.schedule_task_async(task)

asyncio.run(main())
```

**Advanced features**: `AgentManager` also exposes low-level utilities for zero-copy memory mapping (`mmap_file`, `register_object`) and task-graph submission (`submit_graph` with `TaskNode`), which model the concepts of an Agent-OS hardware architecture.

---

### Standards Discovery

`agentos.discover_standards` scans a Python codebase and returns a summary dictionary capturing coding conventions such as line lengths, docstring coverage, and variable naming style.

```python
from agentos import discover_standards

standards = discover_standards("./my_project")
print(standards)
# {
#   "max_line_length": 88,
#   "average_line_length": 42.5,
#   "functions_with_docstrings": 0.85,
#   "variable_naming_style": "snake_case",
#   "files_scanned": 12
# }
```

The returned dictionary can be serialized to JSON and stored for reuse.

---

### Specification Shaping

`agentos.Spec` provides a simple model for feature or product specifications. Specs can be rendered to markdown and enriched with discovered coding standards.

```python
from agentos import Spec, discover_standards

spec = Spec(title="My Feature", description="Adds new capability X")
spec.add_item("Implement the core logic")
spec.add_item("Write unit tests")

# Render to plain markdown
print(spec.to_markdown())

# Optionally enrich with coding standards
standards = discover_standards(".")
print(spec.to_markdown(include_standards=standards))

# Serialize / deserialize
data = spec.to_dict()
restored = Spec.from_dict(data)
```

`agentos.inject_standards` can also be used standalone to append a standards section to any markdown text:

```python
from agentos import inject_standards, discover_standards

text = "# My Spec\n\nSome description."
standards = discover_standards(".")
enriched = inject_standards(text, standards)
```

---

## CLI Reference

AgentOS ships a command-line interface accessible via `agentos` (after installation) or `python -m agentos`.

### `discover` — Scan for coding standards

```
agentos discover [--path DIR] [--output FILE]
```

| Option      | Description                                        | Default |
|-------------|----------------------------------------------------|---------|
| `--path`    | Directory to scan for Python files                 | `.`     |
| `--output`  | File path to write the JSON standards output       | stdout  |

**Example:**

```bash
agentos discover --path ./src --output standards.json
```

---

### `spec` — Create a specification

```
agentos spec --title TITLE [--description TEXT] [--item ITEM ...] [--output FILE]
```

| Option          | Description                                        | Default |
|-----------------|----------------------------------------------------|---------|
| `--title`       | Title of the specification (**required**)          |         |
| `--description` | Description text                                   |         |
| `--item`        | Add an item (can be repeated)                      |         |
| `--output`      | File to write the markdown spec                    | stdout  |

**Example:**

```bash
agentos spec \
  --title "User Auth" \
  --description "Implement user authentication" \
  --item "Add login endpoint" \
  --item "Add logout endpoint" \
  --output spec.md
```

---

### `inject` — Inject standards into a spec

```
agentos inject --spec FILE --standards FILE [--output FILE]
```

| Option        | Description                                                  | Default |
|---------------|--------------------------------------------------------------|---------|
| `--spec`      | Path to the markdown specification file (**required**)       |         |
| `--standards` | Path to the standards JSON file (**required**)               |         |
| `--output`    | File to write the updated specification                      | stdout  |

**Example:**

```bash
agentos inject \
  --spec spec.md \
  --standards standards.json \
  --output spec_with_standards.md
```

---

## Project Layout

```
agentos/
├── README.md              – Project overview
├── CHANGELOG.md           – Release history
├── CONTRIBUTING.md        – Contribution guidelines
├── LICENSE                – Apache 2.0 license
├── pyproject.toml         – Build configuration and tool settings
├── setup.py               – Legacy setuptools entry point
├── requirements.txt       – Optional development requirements
├── agentos/               – Source root (acts as a src-layout)
│   └── agentos/           – Python package
│       ├── __init__.py    – Package initialiser & public API
│       ├── __main__.py    – CLI entry point
│       ├── agent.py       – Agent class
│       ├── task.py        – Task dataclass
│       ├── manager.py     – AgentManager with priority queue
│       ├── standards.py   – Standards discovery & injection
│       ├── spec.py        – Spec model
│       └── utils.py       – Miscellaneous helpers
├── tests/                 – Test suite
└── wiki/                  – This wiki
    ├── Home.md            – Main wiki page (this file)
    └── Release-Notes.md   – Detailed release notes
```

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for the full guide. A quick summary:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Install** in development mode and install dev dependencies:
   ```bash
   pip install -e .
   pip install black isort mypy pytest
   ```

3. **Develop** your changes and ensure everything passes:
   ```bash
   python -m pytest tests/ -v
   mypy agentos/
   black --check agentos/ tests/
   isort --check-only agentos/ tests/
   ```

4. **Submit** a pull request with a clear description of your changes.

### Code style

| Tool    | Purpose             | Configuration        |
|---------|---------------------|----------------------|
| Black   | Code formatting     | `line-length = 88`   |
| isort   | Import ordering     | `profile = "black"`  |
| mypy    | Static type checking| strict mode          |

All public functions and classes should include docstrings.

---

## Release Notes

See [Release-Notes.md](Release-Notes.md) for the full release history, or the [CHANGELOG](../CHANGELOG.md) for a compact summary.

### Latest: v0.1.0 (2026-04-06)

The first public release of AgentOS. Highlights include:

- `Agent`, `Task`, and `AgentManager` abstractions
- Synchronous and `asyncio`-based task execution
- Priority-queue task scheduling with a background worker thread
- `discover_standards` and `inject_standards` for coding conventions
- `Spec` model with markdown rendering and standards integration
- `agentos` CLI with `discover`, `spec`, and `inject` subcommands
- Full type annotations and strict mypy compliance
- Comprehensive test suite

---

## License

AgentOS is licensed under the [Apache License 2.0](../LICENSE).
