# Claude SDK Rust Bindings - Python Tests

This directory contains comprehensive tests for the Claude SDK Rust bindings to ensure they work identically to the Python SDK.

## Test Structure

- `test_session.py` - Tests for the Session class
  - Loading sessions from JSONL files
  - Session properties (total_cost, duration, etc.)
  - Session methods (get_messages_by_role, filter_messages, etc.)
  - Iteration and indexing

- `test_message.py` - Tests for the Message class
  - Message properties
  - Content extraction methods (get_text_blocks, get_tool_blocks)
  - Tool use detection
  - Token information

- `test_project.py` - Tests for the Project class
  - Loading projects
  - Project properties and aggregation
  - Session filtering and analysis
  - Tool usage summaries

- `test_functions.py` - Tests for utility functions
  - find_sessions()
  - find_projects()
  - load_project()
  - Error handling

- `test_integration.py` - End-to-end integration tests
  - Complete workflows
  - Real-world scenarios
  - Performance testing

## Running Tests

From the `python/` directory:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_session.py

# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_session.py::TestSessionLoading::test_load_valid_session
```

## Test Fixtures

The `fixtures/` directory contains test JSONL files copied from the Python SDK tests:
- `empty_session.jsonl` - Empty session file
- `realistic_session.jsonl` - Realistic coding session
- `complex_branching_session.jsonl` - Session with branching
- `tool_only_session.jsonl` - Session with only tool use
- `malformed_session.jsonl` - Malformed data for error testing
- `interrupted_session.jsonl` - Incomplete session

## Requirements

- pytest
- claude-sdk (the Rust bindings)

## API Compatibility

These tests ensure the Rust bindings maintain exact API compatibility with the Python SDK, including:
- Same method names and signatures
- Same property names
- Same return types and behaviors
- Same error messages and exceptions