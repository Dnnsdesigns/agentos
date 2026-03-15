"""Tests for the Spec class."""
import unittest

from agentos.spec import Spec


class TestSpec(unittest.TestCase):
    """Test cases for Spec functionality."""

    def test_spec_initialization(self):
        """Test that spec initializes correctly."""
        spec = Spec(title="TestSpec", description="A test specification")

        self.assertEqual(spec.title, "TestSpec")
        self.assertEqual(spec.description, "A test specification")
        self.assertEqual(spec.items, [])

    def test_spec_with_steps(self):
        """Test spec with predefined items."""
        items = ["Step 1", "Step 2", "Step 3"]
        spec = Spec(title="TestSpec", description="A test spec", items=items)

        self.assertEqual(spec.items, items)

    def test_spec_add_step(self):
        """Test adding items to a spec."""
        spec = Spec(title="TestSpec", description="A test specification")

        spec.add_item("First step")
        spec.add_item("Second step")

        self.assertEqual(spec.items, ["First step", "Second step"])

    def test_spec_to_dict(self):
        """Test converting spec to dictionary."""
        spec = Spec(
            title="TestSpec",
            description="A test specification",
            items=["Step 1", "Step 2"]
        )

        expected_dict = {
            "title": "TestSpec",
            "description": "A test specification",
            "items": ["Step 1", "Step 2"]
        }

        self.assertEqual(spec.to_dict(), expected_dict)

    def test_spec_from_dict(self):
        """Test creating spec from dictionary."""
        data = {
            "title": "TestSpec",
            "description": "A test specification",
            "items": ["Step 1", "Step 2"]
        }

        spec = Spec.from_dict(data)

        self.assertEqual(spec.title, "TestSpec")
        self.assertEqual(spec.description, "A test specification")
        self.assertEqual(spec.items, ["Step 1", "Step 2"])


if __name__ == "__main__":
    unittest.main()