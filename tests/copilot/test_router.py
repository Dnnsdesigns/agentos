"""Tests for agentos.copilot.router."""

from __future__ import annotations

import unittest

from agentos.copilot.router import (
    DiscoverIntent,
    HelpIntent,
    InjectIntent,
    RunIntent,
    SpecIntent,
    parse_intent,
)


def _msg(text: str) -> list:
    """Build a minimal messages list with a single user message."""
    return [{"role": "user", "content": text}]


class TestParseIntentDiscover(unittest.TestCase):
    """Tests for DiscoverIntent parsing."""

    def test_bare_discover(self) -> None:
        intent = parse_intent(_msg("discover"))
        self.assertIsInstance(intent, DiscoverIntent)
        self.assertEqual(intent.path, ".")

    def test_discover_with_positional_path(self) -> None:
        intent = parse_intent(_msg("discover src/"))
        self.assertIsInstance(intent, DiscoverIntent)
        self.assertEqual(intent.path, "src/")

    def test_discover_with_key_value_path(self) -> None:
        intent = parse_intent(_msg("discover path=my_project"))
        self.assertIsInstance(intent, DiscoverIntent)
        self.assertEqual(intent.path, "my_project")

    def test_discover_quoted_path(self) -> None:
        intent = parse_intent(_msg('discover path="my project/src"'))
        self.assertIsInstance(intent, DiscoverIntent)
        self.assertEqual(intent.path, "my project/src")

    def test_discover_case_insensitive(self) -> None:
        intent = parse_intent(_msg("DISCOVER src/"))
        self.assertIsInstance(intent, DiscoverIntent)


class TestParseIntentSpec(unittest.TestCase):
    """Tests for SpecIntent parsing."""

    def test_spec_with_title(self) -> None:
        intent = parse_intent(_msg('spec title="My Feature"'))
        self.assertIsInstance(intent, SpecIntent)
        self.assertEqual(intent.title, "My Feature")

    def test_spec_default_title(self) -> None:
        intent = parse_intent(_msg("spec"))
        self.assertIsInstance(intent, SpecIntent)
        self.assertEqual(intent.title, "Untitled Spec")

    def test_spec_with_description(self) -> None:
        intent = parse_intent(_msg('spec title="T" desc="Does X"'))
        self.assertIsInstance(intent, SpecIntent)
        self.assertEqual(intent.description, "Does X")

    def test_spec_with_items(self) -> None:
        intent = parse_intent(_msg('spec title="T" item="Step 1" item="Step 2"'))
        self.assertIsInstance(intent, SpecIntent)
        self.assertIn("Step 1", intent.items)
        self.assertIn("Step 2", intent.items)

    def test_spec_no_items(self) -> None:
        intent = parse_intent(_msg('spec title="T"'))
        self.assertIsInstance(intent, SpecIntent)
        self.assertEqual(intent.items, [])


class TestParseIntentInject(unittest.TestCase):
    """Tests for InjectIntent parsing."""

    def test_inject_with_paths(self) -> None:
        intent = parse_intent(_msg("inject spec=spec.md standards=std.json"))
        self.assertIsInstance(intent, InjectIntent)
        self.assertEqual(intent.spec_path, "spec.md")
        self.assertEqual(intent.standards_path, "std.json")

    def test_inject_defaults(self) -> None:
        intent = parse_intent(_msg("inject"))
        self.assertIsInstance(intent, InjectIntent)
        self.assertEqual(intent.spec_path, "spec.md")
        self.assertEqual(intent.standards_path, "standards.json")

    def test_inject_quoted_paths(self) -> None:
        intent = parse_intent(_msg('inject spec="my spec.md" standards="my std.json"'))
        self.assertIsInstance(intent, InjectIntent)
        self.assertEqual(intent.spec_path, "my spec.md")
        self.assertEqual(intent.standards_path, "my std.json")


class TestParseIntentRun(unittest.TestCase):
    """Tests for RunIntent parsing."""

    def test_run_with_code(self) -> None:
        intent = parse_intent(_msg('run code="def run(): return 1"'))
        self.assertIsInstance(intent, RunIntent)
        self.assertIn("def run", intent.code)

    def test_run_defaults(self) -> None:
        intent = parse_intent(_msg("run"))
        self.assertIsInstance(intent, RunIntent)
        self.assertEqual(intent.agent_name, "CopilotAgent")
        self.assertEqual(intent.task_description, "Execute code")

    def test_run_custom_agent(self) -> None:
        intent = parse_intent(_msg('run agent="MyBot" task="greet"'))
        self.assertIsInstance(intent, RunIntent)
        self.assertEqual(intent.agent_name, "MyBot")
        self.assertEqual(intent.task_description, "greet")


class TestParseIntentHelp(unittest.TestCase):
    """Tests for HelpIntent parsing."""

    def test_explicit_help(self) -> None:
        intent = parse_intent(_msg("help"))
        self.assertIsInstance(intent, HelpIntent)

    def test_unknown_command_falls_back_to_help(self) -> None:
        intent = parse_intent(_msg("what can you do?"))
        self.assertIsInstance(intent, HelpIntent)

    def test_empty_message_falls_back_to_help(self) -> None:
        intent = parse_intent(_msg(""))
        self.assertIsInstance(intent, HelpIntent)

    def test_empty_messages_list(self) -> None:
        intent = parse_intent([])
        self.assertIsInstance(intent, HelpIntent)

    def test_content_as_list_of_parts(self) -> None:
        """Copilot may send content as a list of content-part dicts."""
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "discover src/"}]}
        ]
        intent = parse_intent(messages)
        self.assertIsInstance(intent, DiscoverIntent)
        self.assertEqual(intent.path, "src/")

    def test_only_assistant_messages_falls_back_to_help(self) -> None:
        messages = [{"role": "assistant", "content": "Hello!"}]
        intent = parse_intent(messages)
        self.assertIsInstance(intent, HelpIntent)


if __name__ == "__main__":
    unittest.main()
