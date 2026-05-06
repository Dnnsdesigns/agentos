"""
Intent handlers for the AgentOS Copilot Extension.

Each handler accepts a typed intent produced by :mod:`agentos.copilot.router`
and returns an iterable of text chunks.  The chunks are fed into
:func:`agentos.copilot.sse.stream_response` to produce the SSE stream that
Copilot expects.

All handlers are synchronous generators (``yield``-based) so they work
seamlessly with the async SSE wrapper and can be unit-tested without an
event loop.

Handlers summary
----------------
* :func:`handle_discover` – run ``discover_standards`` and format results.
* :func:`handle_spec` – create a ``Spec``, render to markdown.
* :func:`handle_inject` – load files, inject standards, return updated spec.
* :func:`handle_run` – exec user-supplied code as an Agent task and run it.
* :func:`handle_help` – return usage information.
* :func:`dispatch` – route an :class:`~agentos.copilot.router.Intent` to the
  appropriate handler.
"""

from __future__ import annotations

import json
from typing import Generator, Iterable

from ..spec import Spec
from ..standards import discover_standards, inject_standards
from ..agent import Agent
from ..task import Task
from .router import (
    DiscoverIntent,
    HelpIntent,
    InjectIntent,
    Intent,
    RunIntent,
    SpecIntent,
)

# Type alias for all handler return types
Chunks = Generator[str, None, None]

# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

_HELP_TEXT = """\
# AgentOS Copilot Extension

Available commands:

| Command | Description | Example |
|---------|-------------|---------|
| `discover [path]` | Scan a directory for coding standards | `@agentos discover src/` |
| `spec title="..." [desc="..."] [item="..."]` | Create a spec | `@agentos spec title="Auth feature"` |
| `inject spec=<file> standards=<file>` | Inject standards into a spec | `@agentos inject spec=spec.md standards=std.json` |
| `run [agent="..."] [task="..."] code="..."` | Run Python code as an agent task | `@agentos run code="def run(): return 42"` |
| `help` | Show this help message | `@agentos help` |
"""


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_help() -> Chunks:
    """Yield the help text in a single chunk.

    Yields
    ------
    str
        The help markdown string.
    """
    yield _HELP_TEXT


def handle_discover(intent: DiscoverIntent) -> Chunks:
    """Discover coding standards in a directory and format them as markdown.

    Parameters
    ----------
    intent:
        A :class:`~agentos.copilot.router.DiscoverIntent` containing the
        directory path to scan.

    Yields
    ------
    str
        A header chunk, then one line per discovered standard.
    """
    try:
        standards = discover_standards(intent.path)
    except Exception as exc:
        yield f"⚠️ Error scanning `{intent.path}`: {exc}\n"
        return

    yield f"## Coding Standards – `{intent.path}`\n\n"
    yield f"Scanned **{standards.get('files_scanned', 0)}** Python files.\n\n"
    for key, value in standards.items():
        if key == "files_scanned":
            continue
        label = key.replace("_", " ").title()
        yield f"- **{label}**: {value}\n"


def handle_spec(intent: SpecIntent) -> Chunks:
    """Create a Spec and render it to markdown.

    Parameters
    ----------
    intent:
        A :class:`~agentos.copilot.router.SpecIntent` describing the spec.

    Yields
    ------
    str
        The rendered markdown spec.
    """
    spec = Spec(
        title=intent.title,
        description=intent.description,
        items=list(intent.items),
    )
    yield spec.to_markdown()
    yield "\n"


def handle_inject(intent: InjectIntent) -> Chunks:
    """Load a spec file and a standards JSON file, inject, and return result.

    Parameters
    ----------
    intent:
        An :class:`~agentos.copilot.router.InjectIntent` with paths to the
        spec and standards files.

    Yields
    ------
    str
        Status messages followed by the updated spec content.
    """
    try:
        with open(intent.spec_path, "r", encoding="utf-8") as f:
            spec_text = f.read()
    except OSError as exc:
        yield f"⚠️ Cannot open spec file `{intent.spec_path}`: {exc}\n"
        return

    try:
        with open(intent.standards_path, "r", encoding="utf-8") as f:
            standards = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        yield f"⚠️ Cannot load standards file `{intent.standards_path}`: {exc}\n"
        return

    result = inject_standards(spec_text, standards)
    yield f"## Updated Spec – `{intent.spec_path}`\n\n"
    yield "```markdown\n"
    yield result
    yield "\n```\n"


def handle_run(intent: RunIntent) -> Chunks:
    """Execute user-supplied Python code as an AgentOS task.

    The ``code`` field must define a ``run()`` function.  AgentOS wraps that
    function in a :class:`~agentos.task.Task` and executes it inside a
    sandboxed namespace.  Only the Python builtins are available in that
    namespace; no imports are permitted unless the user's code contains its
    own ``import`` statements inside the function body.

    .. warning::
        This executes arbitrary Python code.  In a production deployment you
        should run the extension in an isolated container or sandbox
        environment and validate/restrict user input before reaching this
        handler.

    Parameters
    ----------
    intent:
        A :class:`~agentos.copilot.router.RunIntent` with agent name, task
        description, and Python source code.

    Yields
    ------
    str
        Progress messages and the string representation of the task result.
    """
    if not intent.code.strip():
        yield "⚠️ No code provided. Use `code=\"def run(): return 42\"`.\n"
        return

    # Restrict builtins available to user code to a safe subset.
    _SAFE_BUILTINS = {
        name: getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__, name, None)
        for name in (
            "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable",
            "chr", "dict", "dir", "divmod", "enumerate", "filter", "float",
            "format", "frozenset", "getattr", "hasattr", "hash", "hex", "int",
            "isinstance", "issubclass", "iter", "len", "list", "map", "max",
            "min", "next", "object", "oct", "ord", "pow", "print", "range",
            "repr", "reversed", "round", "set", "setattr", "slice", "sorted",
            "str", "sum", "tuple", "type", "zip",
        )
        if getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__, name, None)
        is not None
    }

    namespace: dict = {"__builtins__": _SAFE_BUILTINS}
    try:
        exec(intent.code, namespace)  # noqa: S102
    except Exception as exc:
        yield f"⚠️ Error compiling code: {type(exc).__name__}: {exc}\n"
        return

    run_func = namespace.get("run")
    if run_func is None or not callable(run_func):
        yield "⚠️ The code must define a `run()` function.\n"
        return

    agent = Agent(name=intent.agent_name, description=intent.task_description)
    task = Task(description=intent.task_description, func=run_func)
    agent.add_task(task)

    yield f"▶ Running agent **{intent.agent_name}** …\n\n"
    try:
        results = agent.run_tasks()
    except Exception as exc:
        yield f"⚠️ Task raised an exception: {type(exc).__name__}: {exc}\n"
        return

    for i, result in enumerate(results):
        yield f"**Result {i + 1}:** {result!r}\n"


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def dispatch(intent: Intent) -> Iterable[str]:
    """Route an intent to the appropriate handler and return its chunks.

    Parameters
    ----------
    intent:
        Any intent produced by :func:`agentos.copilot.router.parse_intent`.

    Returns
    -------
    Iterable[str]
        An iterable of text chunks from the matched handler.
    """
    if isinstance(intent, DiscoverIntent):
        return handle_discover(intent)
    if isinstance(intent, SpecIntent):
        return handle_spec(intent)
    if isinstance(intent, InjectIntent):
        return handle_inject(intent)
    if isinstance(intent, RunIntent):
        return handle_run(intent)
    return handle_help()
