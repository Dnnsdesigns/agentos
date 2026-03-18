"""
Command‑line interface for AgentOS.

This module provides a simple CLI for interacting with the AgentOS
framework.  It supports subcommands to discover coding standards,
generate specifications, and inject standards into existing specs.

Examples
--------
Discover standards in a project and write them to JSON::

    python -m agentos discover --path my_project --output standards.json

Create a new specification::

    python -m agentos spec --title "My Feature" --description "Do things"

Inject standards into a spec file::

    python -m agentos inject --spec spec.md --standards standards.json --output spec_with_standards.md
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Callable

from .spec import Spec
from .standards import discover_standards, inject_standards


def _cmd_discover(args: argparse.Namespace) -> int:
    standards = discover_standards(args.path)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(standards, f, indent=2)
    else:
        json.dump(standards, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


def _cmd_spec(args: argparse.Namespace) -> int:
    spec = Spec(title=args.title, description=args.description)
    for item in args.item or []:
        spec.add_item(item)
    md = spec.to_markdown()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
    else:
        print(md)
    return 0


def _cmd_inject(args: argparse.Namespace) -> int:
    # Load spec
    with open(args.spec, "r", encoding="utf-8") as f:
        spec_text = f.read()
    # Load standards
    with open(args.standards, "r", encoding="utf-8") as f:
        standards = json.load(f)
    result = inject_standards(spec_text, standards)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentOS command‑line interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover
    p_discover = subparsers.add_parser("discover", help="Discover coding standards")
    p_discover.add_argument("--path", type=str, default=".", help="Directory to scan")
    p_discover.add_argument("--output", type=str, help="Path to write JSON standards")
    p_discover.set_defaults(func=_cmd_discover)

    # spec
    p_spec = subparsers.add_parser("spec", help="Create a new specification")
    p_spec.add_argument("--title", required=True, help="Title of the specification")
    p_spec.add_argument("--description", help="Description of the specification")
    p_spec.add_argument(
        "--item",
        action="append",
        help="Add an item to the specification (can be repeated)",
    )
    p_spec.add_argument("--output", help="File to write the specification")
    p_spec.set_defaults(func=_cmd_spec)

    # inject
    p_inject = subparsers.add_parser(
        "inject", help="Inject standards into an existing specification"
    )
    p_inject.add_argument(
        "--spec", required=True, help="Path to the specification file"
    )
    p_inject.add_argument(
        "--standards", required=True, help="Path to the standards JSON file"
    )
    p_inject.add_argument(
        "--output",
        help="File to write the updated specification.  If omitted, print to stdout.",
    )
    p_inject.set_defaults(func=_cmd_inject)

    args = parser.parse_args(argv)
    cmd: Callable[[argparse.Namespace], int] = args.func
    return cmd(args)


if __name__ == "__main__":
    raise SystemExit(main())
