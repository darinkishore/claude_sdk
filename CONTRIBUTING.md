# Contributing to Claude SDK

First off, thank you for considering contributing to Claude SDK! It's people like you that make Claude SDK such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps to reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed and what behavior you expected
* Include system details (OS, Python version, Rust version)
* Include any error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain why the enhancement would be useful
* List any alternatives you've considered

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing style
6. Issue that pull request!

## Development Process

### Setting Up Your Environment

```bash
# Clone your fork
git clone https://github.com/yourusername/claude-sdk
cd claude-sdk

# Add upstream remote
git remote add upstream https://github.com/originalrepo/claude-sdk

# Create a virtual environment (Python)
cd python
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev]"

# Build the Rust extension
uv run maturin develop
```

### Code Style

#### Rust
- Follow standard Rust conventions
- Use `cargo fmt` before committing
- Run `cargo clippy` and address warnings
- Add documentation comments for public APIs

#### Python
- Follow PEP 8
- Use type hints for all public functions
- Add docstrings for all public functions and classes
- Run `ruff` for linting and formatting

### Testing

#### Running Tests

```bash
# Rust tests
cargo test

# Python tests
cd python
uv run pytest

# Integration tests (requires Claude CLI)
cargo test --test t1_integration_test -- --ignored --nocapture
```

#### Writing Tests

- Add unit tests for new functionality
- Include integration tests for major features
- Test edge cases and error conditions
- Ensure tests are deterministic

### Documentation

- Update README.md if you change functionality
- Update inline documentation
- Add examples for new features
- Update CHANGELOG.md

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add session export functionality

- Implement JSON, CSV, and Markdown export formats
- Add command-line flags for format selection
- Include comprehensive tests for all formats

Fixes #123
```

## Project Structure

```
claude-sdk/
├── src/                 # Rust source code
│   ├── parser/          # T0: Session parsing
│   ├── execution/       # T1: Execution engine
│   ├── python/          # Python bindings (PyO3)
│   └── types/           # Core data types
├── python/              # Python package
│   ├── claude_sdk/      # Python API layer
│   ├── examples/        # Example scripts
│   └── tests/           # Python tests
├── tests/               # Rust integration tests
└── ai_docs/             # Architecture documentation
```

## Release Process

1. Update version in `Cargo.toml` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a PR with version bump
4. After merge, tag the release
5. Build and publish to PyPI

## Getting Help

- Check the [documentation](docs/)
- Look through [existing issues](https://github.com/yourusername/claude-sdk/issues)
- Join our [discussions](https://github.com/yourusername/claude-sdk/discussions)
- Ask questions in issues with the "question" label

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our contributors page

Thank you for contributing to Claude SDK! 🚀