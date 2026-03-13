"""Tests for the Spec class."""
import unittest

from agentos.spec import Spec


class TestSpec(unittest.TestCase):
    """Test cases for Spec functionality."""

    def test_spec_initialization(self):
        """Test that spec initializes correctly."""
        spec = Spec(name="TestSpec", description="A test specification")

        self.assertEqual(spec.name, "TestSpec")
        self.assertEqual(spec.description, "A test specification")
        self.assertEqual(spec.steps, [])

    def test_spec_with_steps(self):
        """Test spec with predefined steps."""
        steps = ["Step 1", "Step 2", "Step 3"]
        spec = Spec(name="TestSpec", description="A test spec", steps=steps)

        self.assertEqual(spec.steps, steps)

    def test_spec_add_step(self):
        """Test adding steps to a spec."""
        spec = Spec(name="TestSpec", description="A test specification")

        spec.add_step("First step")
        spec.add_step("Second step")

        self.assertEqual(spec.steps, ["First step", "Second step"])

    def test_spec_to_dict(self):
        """Test converting spec to dictionary."""
        spec = Spec(
            name="TestSpec",
            description="A test specification",
            steps=["Step 1", "Step 2"]
        )

        expected_dict = {
            "name": "TestSpec",
            "description": "A test specification",
            "steps": ["Step 1", "Step 2"]
        }

        self.assertEqual(spec.to_dict(), expected_dict)

    def test_spec_from_dict(self):
        """Test creating spec from dictionary."""
        data = {
            "name": "TestSpec",
            "description": "A test specification",
            "steps": ["Step 1", "Step 2"]
        }

        spec = Spec.from_dict(data)

        self.assertEqual(spec.name, "TestSpec")
        self.assertEqual(spec.description, "A test specification")
        self.assertEqual(spec.steps, ["Step 1", "Step 2"])


if __name__ == "__main__":
    unittest.main()