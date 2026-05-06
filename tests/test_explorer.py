"""Tests for the ExplorerAgent class."""

import os
import tempfile
import unittest
from pathlib import Path

from agentos.explorer import ExplorerAgent, FileInfo


def _make_tree(root: str) -> None:
    """Create a small file tree under *root* for testing.

    Layout::

        root/
          a.py          (content: "# a")
          b.txt         (content: "hello")
          sub/
            c.py        (content: "# c")
            d.md        (content: "# d")
          empty/        (empty subdirectory)
    """
    os.makedirs(os.path.join(root, "sub"), exist_ok=True)
    os.makedirs(os.path.join(root, "empty"), exist_ok=True)
    for rel_path, content in [
        ("a.py", "# a"),
        ("b.txt", "hello"),
        ("sub/c.py", "# c"),
        ("sub/d.md", "# d"),
    ]:
        with open(os.path.join(root, rel_path), "w", encoding="utf-8") as f:
            f.write(content)


class TestFileInfo(unittest.TestCase):
    """Tests for the FileInfo dataclass."""

    def test_str_file(self):
        info = FileInfo(path=Path("/tmp/foo.py"), name="foo.py", extension=".py", size=10, is_directory=False)
        self.assertIn("file", str(info))
        self.assertIn("foo.py", str(info))

    def test_str_directory(self):
        info = FileInfo(path=Path("/tmp/bar"), name="bar", extension="", size=0, is_directory=True)
        self.assertIn("dir", str(info))


class TestExplorerAgentInit(unittest.TestCase):
    """Tests for ExplorerAgent construction and repr."""

    def test_default_init(self):
        agent = ExplorerAgent(name="Scout")
        self.assertEqual(agent.name, "Scout")
        self.assertIsNone(agent.description)
        self.assertIsNone(agent.root_path)
        self.assertEqual(agent.tasks, [])

    def test_init_with_root_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = ExplorerAgent(name="Scout", root_path=tmp)
            self.assertEqual(agent.root_path, Path(tmp))

    def test_repr(self):
        agent = ExplorerAgent(name="Scout", root_path="/tmp")
        r = repr(agent)
        self.assertIn("ExplorerAgent", r)
        self.assertIn("Scout", r)


class TestExploreBasic(unittest.TestCase):
    """Tests for the explore() method."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = self._tmpdir.name
        _make_tree(self.root)
        self.agent = ExplorerAgent(name="Scout", root_path=self.root)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_explore_all_files_recursive(self):
        results = self.agent.explore()
        names = {fi.name for fi in results}
        self.assertIn("a.py", names)
        self.assertIn("b.txt", names)
        self.assertIn("c.py", names)
        self.assertIn("d.md", names)
        # No directories by default
        for fi in results:
            self.assertFalse(fi.is_directory)

    def test_explore_with_extensions(self):
        results = self.agent.explore(extensions=[".py"])
        names = {fi.name for fi in results}
        self.assertEqual(names, {"a.py", "c.py"})
        for fi in results:
            self.assertEqual(fi.extension, ".py")

    def test_explore_with_pattern(self):
        results = self.agent.explore(pattern="*.py")
        names = {fi.name for fi in results}
        self.assertEqual(names, {"a.py", "c.py"})

    def test_explore_pattern_takes_precedence_over_extensions(self):
        # pattern="*.txt" should match b.txt even if extensions=[".py"]
        results = self.agent.explore(pattern="*.txt", extensions=[".py"])
        names = {fi.name for fi in results}
        self.assertEqual(names, {"b.txt"})

    def test_explore_non_recursive(self):
        results = self.agent.explore(recursive=False)
        names = {fi.name for fi in results}
        # Only top‑level files; directories excluded by default
        self.assertIn("a.py", names)
        self.assertIn("b.txt", names)
        self.assertNotIn("c.py", names)
        self.assertNotIn("d.md", names)

    def test_explore_include_dirs(self):
        results = self.agent.explore(include_dirs=True, recursive=False)
        names = {fi.name for fi in results}
        self.assertIn("sub", names)
        self.assertIn("empty", names)
        dir_results = [fi for fi in results if fi.is_directory]
        for fi in dir_results:
            self.assertEqual(fi.size, 0)
            self.assertEqual(fi.extension, "")

    def test_explore_explicit_path(self):
        sub = os.path.join(self.root, "sub")
        results = self.agent.explore(sub)
        names = {fi.name for fi in results}
        self.assertEqual(names, {"c.py", "d.md"})

    def test_explore_returns_sorted_results(self):
        results = self.agent.explore()
        paths = [fi.path for fi in results]
        self.assertEqual(paths, sorted(paths))

    def test_explore_stores_last_results(self):
        results = self.agent.explore(extensions=[".py"])
        self.assertEqual(results, self.agent.last_results)

    def test_last_results_is_copy(self):
        self.agent.explore()
        copy = self.agent.last_results
        copy.clear()
        self.assertGreater(len(self.agent.last_results), 0)

    def test_fileinfo_size(self):
        results = self.agent.explore(extensions=[".txt"])
        self.assertEqual(len(results), 1)
        self.assertGreater(results[0].size, 0)


class TestExploreErrors(unittest.TestCase):
    """Tests for error conditions in explore()."""

    def test_no_path_and_no_root_raises(self):
        agent = ExplorerAgent(name="Scout")
        with self.assertRaises(ValueError):
            agent.explore()

    def test_non_directory_path_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            agent = ExplorerAgent(name="Scout")
            with self.assertRaises(NotADirectoryError):
                agent.explore(f.name)

    def test_nonexistent_path_raises(self):
        agent = ExplorerAgent(name="Scout")
        with self.assertRaises(NotADirectoryError):
            agent.explore("/nonexistent/path/xyz")


class TestQueueFileTasks(unittest.TestCase):
    """Tests for the queue_file_tasks() method."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = self._tmpdir.name
        _make_tree(self.root)
        self.agent = ExplorerAgent(name="Scout", root_path=self.root)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_tasks_queued_for_each_file(self):
        collected = []
        found = self.agent.queue_file_tasks(collected.append, extensions=[".py"])
        # Tasks have been queued but not run yet
        self.assertEqual(len(self.agent.tasks), len(found))
        self.assertEqual(len(found), 2)
        self.assertEqual(len(collected), 0)

    def test_tasks_run_and_produce_results(self):
        collected = []
        self.agent.queue_file_tasks(collected.append, extensions=[".py"])
        self.agent.run_tasks()
        self.assertEqual(len(collected), 2)
        names = {fi.name for fi in collected}
        self.assertEqual(names, {"a.py", "c.py"})

    def test_task_descriptions_include_path(self):
        self.agent.queue_file_tasks(lambda fi: None, extensions=[".py"])
        for task in self.agent.tasks:
            self.assertIn("explore:", task.description)

    def test_custom_task_description_prefix(self):
        self.agent.queue_file_tasks(
            lambda fi: None,
            extensions=[".py"],
            task_description_prefix="scan",
        )
        for task in self.agent.tasks:
            self.assertTrue(task.description.startswith("scan:"))

    def test_queue_returns_file_infos(self):
        found = self.agent.queue_file_tasks(lambda fi: None)
        self.assertIsInstance(found, list)
        for fi in found:
            self.assertIsInstance(fi, FileInfo)

    def test_multiple_queues_accumulate(self):
        self.agent.queue_file_tasks(lambda fi: None, extensions=[".py"])
        self.agent.queue_file_tasks(lambda fi: None, extensions=[".txt"])
        self.assertEqual(len(self.agent.tasks), 3)  # 2 py + 1 txt


class TestExplorerAgentInheritance(unittest.TestCase):
    """Ensure ExplorerAgent is a full Agent."""

    def test_is_subclass_of_agent(self):
        from agentos.agent import Agent
        self.assertTrue(issubclass(ExplorerAgent, Agent))

    def test_add_and_run_regular_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = ExplorerAgent(name="Scout", root_path=tmp)
            agent.add_task(lambda: 42)
            results = agent.run_tasks()
            self.assertEqual(results, [42])


class TestExplorerAgentPublicExport(unittest.TestCase):
    """Ensure symbols are importable from the top‑level package."""

    def test_importable_from_package(self):
        import agentos
        self.assertTrue(hasattr(agentos, "ExplorerAgent"))
        self.assertTrue(hasattr(agentos, "FileInfo"))


if __name__ == "__main__":
    unittest.main()
