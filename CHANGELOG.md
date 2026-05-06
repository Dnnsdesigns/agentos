# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `ExplorerAgent` – a specialised `Agent` subclass that traverses directory
  trees to discover files.  Supports filtering by file extension or
  `fnmatch`‑style pattern, recursive/flat traversal, and optional directory
  inclusion.
- `FileInfo` – a dataclass returned by `ExplorerAgent.explore()` holding the
  path, name, extension, size, and directory flag for each discovered entry.
- `ExplorerAgent.queue_file_tasks()` – convenience method that explores a
  directory and queues a handler `Task` for every discovered entry.
- Both `ExplorerAgent` and `FileInfo` are now exported from the top‑level
  `agentos` package.

## [0.1.0] - 2026-04-06

### Added
- Initial release of AgentOS framework
- Agent abstraction with task queuing and execution
- Task management with synchronous and asynchronous execution
- Agent manager for coordinating multiple agents
- Standards discovery and injection functionality
- Specification shaping with standards integration
- CLI interface for common operations
- Comprehensive test suite
- Type hints and documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

[0.1.0]: https://github.com/Dnnsdesigns/agentos/releases/tag/v0.1.0