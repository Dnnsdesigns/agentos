"""
Coding standards discovery and injection.

This module contains utility functions for discovering coding conventions
from an existing codebase and for injecting those standards into text
specifications.  These tools are designed to operate on Python projects
but can be extended for other languages.

The discovery process scans Python files under a given directory and
computes simple metrics that capture aspects of the code style.  These
metrics include maximum and average line lengths, prevalence of docstrings,
and naming patterns for functions and variables.  The result is returned
as a dictionary that can be serialised to JSON.

The injection function takes a specification string and a dictionary of
standards and appends a formatted section summarising the standards.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def discover_standards(path: str | Path) -> Dict[str, object]:
    """Discover simple coding standards from Python files in a directory.

    Parameters
    ----------
    path: str or Path
        The directory to scan.  All `.py` files found recursively under
        this path will be analysed.

    Returns
    -------
    dict
        A dictionary summarising the discovered standards.  Keys include:

        * ``max_line_length`` – The maximum length of any line.
        * ``average_line_length`` – The average length of all lines.
        * ``functions_with_docstrings`` – Fraction of functions with a
          docstring (0–1).
        * ``variable_naming_style`` – Guess of predominant naming style
          (``snake_case`` or ``camelCase``).
    """
    path = Path(path)
    python_files = list(path.rglob("*.py"))
    total_lines = 0
    total_length = 0
    max_length = 0
    total_functions = 0
    functions_with_docstrings = 0
    variable_names: List[str] = []
    for file in python_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                source = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        lines = source.splitlines()
        for line in lines:
            length = len(line)
            total_lines += 1
            total_length += length
            max_length = max(max_length, length)
            # Extract variable assignments via regex (simple heuristic)
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if match:
                variable_names.append(match.group(1))
        # Parse AST to find functions and docstrings
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                doc = ast.get_docstring(node)
                if doc:
                    functions_with_docstrings += 1
    avg_length = total_length / total_lines if total_lines else 0
    docstring_fraction = (
        functions_with_docstrings / total_functions if total_functions else 0
    )
    # Determine naming style
    snake_case_count = 0
    camel_case_count = 0
    camel_re = re.compile(r"[a-z]+(?:[A-Z][a-z0-9]*)+")
    for name in variable_names:
        if "_" in name:
            snake_case_count += 1
        elif camel_re.fullmatch(name):
            camel_case_count += 1
    if snake_case_count > camel_case_count:
        naming_style = "snake_case"
    elif camel_case_count > 0:
        naming_style = "camelCase"
    else:
        naming_style = "undetermined"
    return {
        "max_line_length": max_length,
        "average_line_length": round(avg_length, 2),
        "functions_with_docstrings": round(docstring_fraction, 2),
        "variable_naming_style": naming_style,
        "files_scanned": len(python_files),
    }


def inject_standards(spec_text: str, standards: Dict[str, object]) -> str:
    """Inject discovered standards into a specification.

    The standards are formatted as a markdown list and appended to the end
    of the provided specification.  If the specification already contains
    a ``## Standards`` heading, the standards will be inserted there
    instead.

    Parameters
    ----------
    spec_text: str
        The original specification text.
    standards: dict
        A dictionary of standards produced by :func:`discover_standards`.

    Returns
    -------
    str
        The specification with a standards section appended or updated.
    """
    lines = spec_text.splitlines()
    standards_lines = ["## Coding Standards", ""]
    for key, value in standards.items():
        standards_lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    standards_section = "\n".join(standards_lines) + "\n"
    # Look for existing section
    for idx, line in enumerate(lines):
        if line.strip().lower() == "## coding standards":
            # Replace everything after this line with new standards
            return "\n".join(lines[: idx + 1]) + "\n" + standards_section
    # Otherwise append
    return spec_text.rstrip() + "\n\n" + standards_section
