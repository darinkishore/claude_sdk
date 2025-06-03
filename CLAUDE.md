# Claude SDK Development Guide

A Rust library with Python bindings for parsing and analyzing Claude Code session data.

## Quick Start

### Development Setup

```bash
# Clone and setup
git clone <repo-url>
cd rust_sdk

# Build and install in development mode
cd python
uv build

# Test the installation
python -c "import claude_sdk; print('✅ Import successful!')"
```

## Project Structure

```
rust_sdk/
├── src/                    # Rust source code
│   ├── lib.rs             # Main library entry point
│   ├── python/            # Python bindings (PyO3)
│   │   ├── mod.rs         # Python module registration
│   │   ├── classes.rs     # Python class wrappers
│   │   ├── functions.rs   # Python function exports
│   │   └── ...
│   ├── types/             # Core Rust types
│   ├── parser/            # JSONL parsing logic
│   └── ...
├── python/                # Python package
│   ├── pyproject.toml     # Python build configuration
│   ├── claude_sdk/        # Python package source
│   │   └── __init__.py    # Python API exports
│   └── .venv/             # Python virtual environment
├── Cargo.toml             # Rust dependencies and config
└── tests/                 # Test files
```

## Building

### Rust Library Only

```bash
# Check compilation
cargo check

# Build library
cargo build

# Run Rust tests
cargo test
```

### Python Extension

```bash
cd python

# Development build (installs in current Python env)
uv build

# Production build (creates wheel)
uv build --release

# Build with specific features
uv build --features python
```

## Testing

### Rust Tests

```bash
# Run all Rust tests
cargo test

# Run specific test module
cargo test parser

# Run with output
cargo test -- --nocapture
```

### Python Tests

```bash
cd python

# Install in development mode first
uv build

# Run Python tests (if you have any)
uv run -m pytest tests/

# Quick import test
python -c "import claude_sdk; print('✅ Working!')"
```

### Integration Testing

```bash
# Test with real session file
python -c "
import claude_sdk
session = claude_sdk.load('path/to/session.jsonl')
print(f'Loaded session with {len(session.messages)} messages')
"
```

## Development Workflow

### Making Changes

1. **Rust changes**: Edit files in `src/`
2. **Python binding changes**: Edit files in `src/python/`
3. **Python API changes**: Edit `python/claude_sdk/__init__.py`

### Rebuilding After Changes

```bash
cd python

# Rebuild and reinstall
uv build

# Test your changes
python -c "import claude_sdk; # your test code"
```

### Release Build

```bash
cd python

# Build wheel for distribution
uv build --release

# Wheel will be in ../target/wheels/
ls ../target/wheels/
```

## Configuration Files

### `Cargo.toml`
- **Package name**: `claude-sdk` (matches Python package)
- **Library name**: `claude_sdk` (matches Python import)
- **Python feature**: Enable with `--features python`
- **Excludes**: Top-level `python/` directory from Rust build

### `python/pyproject.toml` 
- **Module name**: `claude_sdk._core` (Rust extension)
- **Python packages**: `["claude_sdk"]`
- **Manifest path**: `../Cargo.toml` (points to Rust config)

## Common Issues & Solutions

### Build Failures

**Error**: `file not found for module 'python'`
- **Solution**: Build from project root or use `uv build` from `python/` directory

**Error**: `PyInit symbol not found`
- **Solution**: Ensure `#[pymodule]` function name matches expected import structure

### Import Failures

- **Solution**: Run `uv build` to rebuild the extension
- **Check**: Make sure you're in the right Python environment

- **Solution**: Use `uv build` instead of `uv build --release` for development

### Development Tips

1. **Use `uv build`** for development - it handles the shared library correctly
2. **Build from `python/` directory** - it has the right context and config
3. **Check imports after changes** - Python extensions need rebuilding after Rust changes
4. **Use `cargo check`** for quick Rust-only validation

## Available Python API

```python
import claude_sdk

# Core functions
session = claude_sdk.load("session.jsonl")
sessions = claude_sdk.find_sessions()
projects = claude_sdk.find_projects()
project = claude_sdk.load_project("project_name")

# Classes
claude_sdk.Session       # Session data
claude_sdk.Message       # Individual messages
claude_sdk.Project       # Project with multiple sessions
claude_sdk.ToolResult    # Tool execution results

# Exceptions
claude_sdk.ClaudeSDKError
claude_sdk.ParseError
claude_sdk.ValidationError
claude_sdk.SessionError
```

## Performance Notes

- Written in Rust for fast JSONL parsing
- Zero-copy string handling where possible
- Efficient conversation threading
- Memory-conscious design for large session files

## Troubleshooting

### Clean Build

```bash
# Clean Rust build cache
cargo clean

# Remove Python build artifacts
rm -rf python/claude_sdk/*.so
rm -rf python/claude_sdk/*.pyi

# Rebuild everything
uv build
```

### Environment Issues

```bash
# Check Python environment
python -c "import sys; print(sys.executable)"

# Check if package is installed
pip list | grep claude

# Reinstall if needed
pip uninstall claude-sdk
uv build
```

## Development Memories

- ALWAYS use uv run before typing python. it sets up the environment properly. Use `uv add` to add packages. 
- Use uv build to build the project. 