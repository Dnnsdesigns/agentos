"""
Intent model and message router for the AgentOS Copilot Extension.

This module parses incoming Copilot chat messages and maps them to structured
``Intent`` objects that the handler layer can act on.  The routing is done
using simple keyword and regex matching so that no additional LLM call is
required.

Supported commands (all case-insensitive):

+-----------+--------------------------------------------------+
| Command   | Example message                                  |
+===========+==================================================+
| discover  | ``discover src/`` or ``discover path=src/``      |
+-----------+--------------------------------------------------+
| spec      | ``spec title="My Feature" desc="Does X"``        |
+-----------+--------------------------------------------------+
| inject    | ``inject spec=spec.md standards=std.json``       |
+-----------+--------------------------------------------------+
| run       | ``run agent=MyAgent task="Do it" code=...``      |
+-----------+--------------------------------------------------+
| help      | ``help`` or anything unrecognised                |
+-----------+--------------------------------------------------+

Any message that does not match a recognised command pattern will produce a
:class:`HelpIntent` so the user always receives useful feedback.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Intent dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DiscoverIntent:
    """Intent to run :func:`agentos.standards.discover_standards`.

    Parameters
    ----------
    path:
        The directory path to scan.  Defaults to ``"."`` if the user omits it.
    """

    path: str = "."


@dataclass
class SpecIntent:
    """Intent to create a :class:`agentos.spec.Spec` and render it.

    Parameters
    ----------
    title:
        The spec title.
    description:
        An optional longer description.
    items:
        Optional list of spec items to include.
    """

    title: str
    description: Optional[str] = None
    items: List[str] = field(default_factory=list)


@dataclass
class InjectIntent:
    """Intent to call :func:`agentos.standards.inject_standards`.

    Parameters
    ----------
    spec_path:
        Path to the specification markdown file.
    standards_path:
        Path to the JSON standards file produced by ``discover``.
    """

    spec_path: str
    standards_path: str


@dataclass
class RunIntent:
    """Intent to create an Agent, add a task, and run it.

    Parameters
    ----------
    agent_name:
        Name for the ephemeral agent.
    task_description:
        Human-readable description of the task.
    code:
        Python source of a ``run()`` function that will be exec'd and called.
    """

    agent_name: str
    task_description: str
    code: str


@dataclass
class HelpIntent:
    """Fallback intent – show usage information."""


# Union type alias for all intents
Intent = Union[DiscoverIntent, SpecIntent, InjectIntent, RunIntent, HelpIntent]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _last_user_message(messages: List[dict]) -> str:
    """Return the content of the most recent user message, or empty string."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Copilot may send content as a list of content parts
            if isinstance(content, list):
                parts = [p.get("text", "") for p in content if isinstance(p, dict)]
                return " ".join(parts).strip()
            return str(content).strip()
    return ""


def _extract_value(text: str, *keys: str) -> Optional[str]:
    """Extract the first matching key=value or key="quoted value" pair.

    Parameters
    ----------
    text:
        The full message text to search.
    *keys:
        One or more key names to look for (checked in order).

    Returns
    -------
    str or None
        The unquoted value if found, otherwise ``None``.
    """
    for key in keys:
        # Match key="value with spaces" or key=value
        pattern = rf'(?:^|\s){re.escape(key)}=["\']([^"\']+)["\']'
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)
        # Unquoted value (stops at whitespace)
        pattern2 = rf'(?:^|\s){re.escape(key)}=(\S+)'
        m2 = re.search(pattern2, text, re.IGNORECASE)
        if m2:
            return m2.group(1)
    return None


def _extract_items(text: str) -> List[str]:
    """Extract repeated ``item=...`` values from a message."""
    items: List[str] = []
    for m in re.finditer(r'item=["\']([^"\']+)["\']', text, re.IGNORECASE):
        items.append(m.group(1))
    # Also handle plain item=word
    for m in re.finditer(r'item=(\S+)', text, re.IGNORECASE):
        value = m.group(1)
        if value not in items:
            items.append(value)
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_intent(messages: List[dict]) -> Intent:
    """Parse a list of Copilot chat messages and return a structured intent.

    The function examines the last user message and applies a series of
    pattern-matching rules to determine what the user wants.  Unrecognised
    messages fall back to :class:`HelpIntent`.

    Parameters
    ----------
    messages:
        The ``messages`` array from a Copilot API request body.  Each
        element is a dict with at least ``"role"`` and ``"content"`` keys.

    Returns
    -------
    Intent
        One of :class:`DiscoverIntent`, :class:`SpecIntent`,
        :class:`InjectIntent`, :class:`RunIntent`, or :class:`HelpIntent`.
    """
    text = _last_user_message(messages)
    text_lower = text.lower()

    # --- discover ---
    if re.search(r'\bdiscover\b', text_lower):
        path = _extract_value(text, "path") or "."
        # Also handle bare "discover <path>" without a key
        if path == ".":
            m = re.search(r'\bdiscover\s+([^\s=]+)', text, re.IGNORECASE)
            if m and "=" not in m.group(1):
                path = m.group(1)
        return DiscoverIntent(path=path)

    # --- inject (must be checked before spec, since inject messages contain the word "spec") ---
    if re.search(r'\binject\b', text_lower):
        spec_path = _extract_value(text, "spec") or "spec.md"
        standards_path = _extract_value(text, "standards") or "standards.json"
        return InjectIntent(spec_path=spec_path, standards_path=standards_path)

    # --- spec ---
    if re.search(r'\bspec\b', text_lower):
        title = _extract_value(text, "title") or "Untitled Spec"
        description = _extract_value(text, "desc", "description")
        items = _extract_items(text)
        return SpecIntent(title=title, description=description, items=items)

    # --- run ---
    if re.search(r'\brun\b', text_lower):
        agent_name = _extract_value(text, "agent") or "CopilotAgent"
        task_description = _extract_value(text, "task") or "Execute code"
        code = _extract_value(text, "code") or ""
        return RunIntent(
            agent_name=agent_name,
            task_description=task_description,
            code=code,
        )

    # --- help (explicit or fallback) ---
    return HelpIntent()
