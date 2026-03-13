"""
Specification model for AgentOS.

This module defines a simple :class:`Spec` class used to represent
product or feature specifications.  A specification includes a title,
an optional description, and an optional list of features or tasks.  It
provides methods to render itself to markdown and to incorporate coding
standards discovered by :func:`agentos.standards.discover_standards`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .standards import inject_standards


@dataclass
class Spec:
    """Represents a high‑level specification for an agentic project.

    Parameters
    ----------
    title: str
        The name of the feature or product being specified.
    description: str, optional
        A longer description of the purpose and goals.
    items: list of str, optional
        A list of specification items, such as required tasks or features.
    """

    title: str
    description: Optional[str] = None
    items: List[str] = field(default_factory=list)

    def to_markdown(self, include_standards: Optional[dict] = None) -> str:
        """Render the specification to a markdown string.

        If a standards dictionary is provided, the resulting markdown will
        include a section listing the standards.  See
        :func:`agentos.standards.inject_standards` for formatting.

        Parameters
        ----------
        include_standards: dict, optional
            A dictionary of coding standards.  If provided, these will be
            appended to the markdown output.

        Returns
        -------
        str
            The specification rendered as markdown.
        """
        lines: List[str] = [f"# {self.title}"]
        if self.description:
            lines.append("")
            lines.append(self.description)
        if self.items:
            lines.append("")
            lines.append("## Items")
            for item in self.items:
                lines.append(f"- {item}")
        md = "\n".join(lines)
        if include_standards:
            md = inject_standards(md, include_standards)
        return md

    def add_item(self, item: str) -> None:
        """Add a new item to the specification."""
        self.items.append(item)
