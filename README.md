# AgentOS

AgentOS is a lightweight framework for building and managing autonomous AI agents.

The goal of AgentOS is to provide a simple but extensible foundation for creating
agentic systems.  It abstracts common concerns – such as task scheduling,
standards discovery, and specification shaping – into reusable components that
work with any underlying model or tooling.  While it is inspired by the idea of
"spec‑driven development," it is not tied to any particular AI provider.  The
core objects are plain Python classes with clear interfaces, making it easy to
extend or swap out implementations.

## Highlights

* **Agent abstraction** – Define agents with names, descriptions, and a queue of
  tasks to run.  Agents can be extended to add custom behaviours.
* **Task management** – Represent discrete units of work as `Task` objects.
  Tasks can wrap arbitrary callables and are executed in the order they are
  queued.
* **Agent manager** – Coordinate a collection of agents, schedule tasks, and
  persist agent state.  The manager supports asynchronous execution using
  Python's `asyncio` but can also operate synchronously.
* **Standards discovery** – Scan a codebase and extract conventions and
  patterns into a structured dictionary.  This allows you to encode your
  coding standards and reuse them when generating new code or specifications.
* **Specification shaping** – Create and manipulate specs that describe
  high‑level plans for your agents.  Specs can incorporate discovered
  standards to ensure alignment across your project.

## Installation

```bash
pip install -e .
```

## Usage

```python
from agentos import Agent, Task, AgentManager

# Create an agent
agent = Agent(name="MyAgent", description="An example agent")

# Create and queue tasks
task = Task(callable=my_function, args=(arg1, arg2))
agent.queue_task(task)

# Run with a manager
manager = AgentManager()
manager.add_agent(agent)
manager.run()
```

## Project Layout

```
agentos/
├── README.md          – This file
├── agentos/           – Python package containing the core framework
│   ├── __init__.py    – Package initialiser
│   ├── __main__.py    – CLI entrypoint for running AgentOS commands
│   ├── agent.py       – Defines the `Agent` class
│   ├── task.py        – Defines the `Task` class
│   ├── manager.py     – Implements the `AgentManager`
│   ├── standards.py   – Functions for discovering and injecting standards
│   ├── spec.py        – A simple specification model
│   └── utils.py       – Miscellaneous helper functions
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
