# Claude SDK - High-Performance Python Bindings

A high-performance Python SDK for Claude Code, implemented in Rust for blazing-fast parsing and processing of Claude conversation data.

## Features

- **🚀 Performance**: Built with Rust for 10-100x faster parsing compared to pure Python
- **🔒 Type Safety**: Full type annotations and runtime type checking
- **💾 Memory Efficient**: Streaming parser handles large conversation files efficiently
- **🐍 Pythonic API**: Familiar interface matching the original Claude Code SDK
- **🛡️ Thread Safe**: Safe concurrent access from multiple Python threads

## Installation

```bash
pip install claude-sdk
```

## Quick Start

```python
from claude_sdk import load, find_sessions, find_projects

# Load a session from a JSONL file
session = load("path/to/conversation.jsonl")

# Access session metadata
print(f"Session ID: {session.id}")
print(f"Created: {session.created_at}")
print(f"Total messages: {len(session.messages)}")

# Iterate through messages
for message in session.messages:
    print(f"{message.role}: {message.get_text()}")

# Find all sessions in a directory
sessions = find_sessions("/path/to/claude/sessions")
for session_path in sessions:
    session = load(session_path)
    print(f"Found session: {session.id}")

# Work with projects
projects = find_projects()
for project_id, project_path in projects.items():
    project = load_project(project_id)
    print(f"Project: {project.name} ({project.sessions} sessions)")
```

## Performance Benefits

This Rust-based implementation provides significant performance improvements:

- **Parsing**: 10-100x faster than pure Python JSON parsing
- **Memory**: Efficient streaming reduces memory usage for large files
- **Concurrency**: Native thread safety allows parallel processing
- **Startup**: Fast import times with pre-compiled native extension

## API Compatibility

This package maintains full API compatibility with the original Claude Code SDK, making migration seamless. Simply replace your import:

```python
# Before
from claude_code_sdk import load, find_sessions

# After
from claude_sdk import load, find_sessions
```

## Requirements

- Python 3.8 or higher
- Compatible with Windows, macOS, and Linux

## License

MIT License - see LICENSE file for details