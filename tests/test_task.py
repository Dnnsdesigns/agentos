"""Tests for the Task class."""

import unittest

from agentos.task import Task


class TestTask(unittest.TestCase):
    """Test cases for Task functionality."""

    def test_task_initialization(self):
        """Test that task initializes correctly."""

        def dummy_func():
            return "test"

        task = Task(
            description="dummy", func=dummy_func, args=(1, 2), kwargs={"key": "value"}
        )

        self.assertEqual(task.func, dummy_func)
        self.assertEqual(task.args, (1, 2))
        self.assertEqual(task.kwargs, {"key": "value"})

    def test_task_execution_success(self):
        """Test successful task execution."""

        def add_numbers(a, b):
            return a + b

        task = Task(description="add", func=add_numbers, args=(3, 5))
        result = task.run()

        self.assertEqual(result, 8)

    def test_task_execution_with_exception(self):
        """Test task execution that raises an exception."""

        def failing_func():
            raise ValueError("Test error")

        task = Task(description="fail", func=failing_func)
        with self.assertRaises(ValueError) as ctx:
            task.run()

        self.assertEqual(str(ctx.exception), "Test error")

    def test_task_with_kwargs(self):
        """Test task execution with keyword arguments."""

        def multiply(a, b, multiplier=1):
            return (a + b) * multiplier

        task = Task(
            description="multiply", func=multiply, args=(2, 3), kwargs={"multiplier": 4}
        )
        result = task.run()

        self.assertEqual(result, 20)  # (2+3) * 4 = 20


if __name__ == "__main__":
    unittest.main()
