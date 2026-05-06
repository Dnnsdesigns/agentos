"""Tests for agentos.copilot.handlers."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch


def _collect(gen) -> str:
    """Collect all chunks from a generator into a single string."""
    return "".join(gen)


class TestHandleHelp(unittest.TestCase):
    """Tests for handle_help."""

    def test_returns_markdown(self) -> None:
        from agentos.copilot.handlers import handle_help

        output = _collect(handle_help())
        self.assertIn("AgentOS", output)
        self.assertIn("discover", output)
        self.assertIn("spec", output)

    def test_yields_at_least_one_chunk(self) -> None:
        from agentos.copilot.handlers import handle_help

        chunks = list(handle_help())
        self.assertGreater(len(chunks), 0)


class TestHandleDiscover(unittest.TestCase):
    """Tests for handle_discover."""

    def test_successful_discover(self) -> None:
        from agentos.copilot.handlers import handle_discover
        from agentos.copilot.router import DiscoverIntent

        fake_standards = {
            "max_line_length": 88,
            "average_line_length": 45.2,
            "functions_with_docstrings": 0.9,
            "variable_naming_style": "snake_case",
            "files_scanned": 5,
        }
        with patch("agentos.copilot.handlers.discover_standards", return_value=fake_standards):
            output = _collect(handle_discover(DiscoverIntent(path="src/")))

        self.assertIn("src/", output)
        self.assertIn("5", output)  # files_scanned
        self.assertIn("snake_case", output)

    def test_error_from_discover(self) -> None:
        from agentos.copilot.handlers import handle_discover
        from agentos.copilot.router import DiscoverIntent

        with patch(
            "agentos.copilot.handlers.discover_standards",
            side_effect=OSError("no such directory"),
        ):
            output = _collect(handle_discover(DiscoverIntent(path="bad_path")))

        self.assertIn("⚠️", output)
        self.assertIn("bad_path", output)


class TestHandleSpec(unittest.TestCase):
    """Tests for handle_spec."""

    def test_renders_title(self) -> None:
        from agentos.copilot.handlers import handle_spec
        from agentos.copilot.router import SpecIntent

        output = _collect(handle_spec(SpecIntent(title="My Feature")))
        self.assertIn("My Feature", output)

    def test_renders_description(self) -> None:
        from agentos.copilot.handlers import handle_spec
        from agentos.copilot.router import SpecIntent

        output = _collect(handle_spec(SpecIntent(title="T", description="Does X")))
        self.assertIn("Does X", output)

    def test_renders_items(self) -> None:
        from agentos.copilot.handlers import handle_spec
        from agentos.copilot.router import SpecIntent

        output = _collect(
            handle_spec(SpecIntent(title="T", items=["Step 1", "Step 2"]))
        )
        self.assertIn("Step 1", output)
        self.assertIn("Step 2", output)


class TestHandleInject(unittest.TestCase):
    """Tests for handle_inject."""

    def _write_temp(self, suffix: str, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, content.encode())
        os.close(fd)
        return path

    def test_successful_inject(self) -> None:
        from agentos.copilot.handlers import handle_inject
        from agentos.copilot.router import InjectIntent

        spec_path = self._write_temp(".md", "# My Spec\n\nSome content.\n")
        standards_path = self._write_temp(
            ".json",
            json.dumps({"max_line_length": 88, "variable_naming_style": "snake_case"}),
        )
        try:
            output = _collect(
                handle_inject(InjectIntent(spec_path=spec_path, standards_path=standards_path))
            )
        finally:
            os.unlink(spec_path)
            os.unlink(standards_path)

        self.assertIn("My Spec", output)
        self.assertIn("snake_case", output)

    def test_missing_spec_file(self) -> None:
        from agentos.copilot.handlers import handle_inject
        from agentos.copilot.router import InjectIntent

        output = _collect(
            handle_inject(
                InjectIntent(spec_path="/nonexistent/spec.md", standards_path="std.json")
            )
        )
        self.assertIn("⚠️", output)

    def test_missing_standards_file(self) -> None:
        from agentos.copilot.handlers import handle_inject
        from agentos.copilot.router import InjectIntent

        spec_path = self._write_temp(".md", "# Spec\n")
        try:
            output = _collect(
                handle_inject(
                    InjectIntent(spec_path=spec_path, standards_path="/nonexistent/std.json")
                )
            )
        finally:
            os.unlink(spec_path)

        self.assertIn("⚠️", output)

    def test_invalid_json_standards(self) -> None:
        from agentos.copilot.handlers import handle_inject
        from agentos.copilot.router import InjectIntent

        spec_path = self._write_temp(".md", "# Spec\n")
        bad_json_path = self._write_temp(".json", "not json!")
        try:
            output = _collect(
                handle_inject(InjectIntent(spec_path=spec_path, standards_path=bad_json_path))
            )
        finally:
            os.unlink(spec_path)
            os.unlink(bad_json_path)

        self.assertIn("⚠️", output)


class TestHandleRun(unittest.TestCase):
    """Tests for handle_run."""

    def test_simple_run(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        code = "def run(): return 42"
        output = _collect(handle_run(RunIntent(agent_name="Bot", task_description="answer", code=code)))
        self.assertIn("42", output)

    def test_no_code_provided(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        output = _collect(handle_run(RunIntent(agent_name="Bot", task_description="t", code="")))
        self.assertIn("⚠️", output)

    def test_syntax_error_in_code(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        code = "def run() return 1"  # missing colon
        output = _collect(handle_run(RunIntent(agent_name="Bot", task_description="t", code=code)))
        self.assertIn("⚠️", output)

    def test_missing_run_function(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        code = "x = 1 + 2"  # no run() function
        output = _collect(handle_run(RunIntent(agent_name="Bot", task_description="t", code=code)))
        self.assertIn("⚠️", output)

    def test_task_raises_exception(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        code = "def run(): raise ValueError('boom')"
        output = _collect(handle_run(RunIntent(agent_name="Bot", task_description="t", code=code)))
        self.assertIn("⚠️", output)

    def test_agent_name_in_output(self) -> None:
        from agentos.copilot.handlers import handle_run
        from agentos.copilot.router import RunIntent

        code = "def run(): return 'hi'"
        output = _collect(
            handle_run(RunIntent(agent_name="MySpecialAgent", task_description="t", code=code))
        )
        self.assertIn("MySpecialAgent", output)


class TestDispatch(unittest.TestCase):
    """Tests for the dispatch function."""

    def test_dispatch_discover(self) -> None:
        from agentos.copilot.handlers import dispatch
        from agentos.copilot.router import DiscoverIntent

        with patch(
            "agentos.copilot.handlers.discover_standards",
            return_value={"files_scanned": 0},
        ):
            output = _collect(dispatch(DiscoverIntent(path=".")))
        self.assertIsInstance(output, str)

    def test_dispatch_help(self) -> None:
        from agentos.copilot.handlers import dispatch
        from agentos.copilot.router import HelpIntent

        output = _collect(dispatch(HelpIntent()))
        self.assertIn("AgentOS", output)


if __name__ == "__main__":
    unittest.main()
