"""Tests for the Agent class."""
import asyncio
import unittest
from unittest.mock import Mock

from agentos.agent import Agent
from agentos.task import Task


class TestAgent(unittest.TestCase):
    """Test cases for Agent functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = Agent(name="TestAgent", description="A test agent")

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        self.assertEqual(self.agent.name, "TestAgent")
        self.assertEqual(self.agent.description, "A test agent")
        self.assertEqual(len(self.agent.tasks), 0)

    def test_queue_task(self):
        """Test queuing a task."""
        def dummy_func():
            return "test"

        task = Task(callable=dummy_func)
        self.agent.queue_task(task)

        self.assertEqual(len(self.agent.tasks), 1)
        self.assertEqual(self.agent.tasks[0], task)

    def test_run_sync(self):
        """Test synchronous task execution."""
        results = []

        def append_result(value):
            results.append(value)

        task1 = Task(callable=append_result, args=(1,))
        task2 = Task(callable=append_result, args=(2,))

        self.agent.queue_task(task1)
        self.agent.queue_task(task2)

        self.agent.run()

        self.assertEqual(results, [1, 2])

    def test_run_async(self):
        """Test asynchronous task execution."""
        async def async_task(value):
            await asyncio.sleep(0.01)
            return value * 2

        task1 = Task(callable=async_task, args=(3,))
        task2 = Task(callable=async_task, args=(4,))

        self.agent.queue_task(task1)
        self.agent.queue_task(task2)

        results = asyncio.run(self.agent.run_async())
        self.assertEqual(results, [6, 8])


if __name__ == "__main__":
    unittest.main()