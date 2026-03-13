# Contributing to AgentOS

Thank you for your interest in contributing to AgentOS! We welcome contributions from the community.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dnnsdesigns/agentos.git
   cd agentos
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e .
   ```

4. **Install development dependencies:**
   ```bash
   pip install black isort mypy pytest
   ```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and ensure tests pass:**
   ```bash
   # Run tests
   python -m pytest

   # Run type checking
   mypy agentos/

   # Format code
   black agentos/ tests/
   isort agentos/ tests/
   ```

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

4. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- **Formatting:** We use [Black](https://black.readthedocs.io/) for code formatting
- **Imports:** We use [isort](https://pycqa.github.io/isort/) for import sorting
- **Type hints:** We use [mypy](https://mypy.readthedocs.io/) for static type checking
- **Line length:** 88 characters (Black's default)

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a PR
- Aim for good test coverage

## Documentation

- Update documentation for any new features
- Use clear, descriptive commit messages
- Add docstrings to new functions and classes

## Issues

- Check existing issues before creating new ones
- Use issue templates when available
- Provide clear reproduction steps for bugs

## License

By contributing to AgentOS, you agree that your contributions will be licensed under the MIT License.