# Claude SDK for Python

A high-performance Python library for parsing and analyzing Claude Code session data. Built with Rust for speed, designed with Python developers in mind.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
  - [Functions](#functions)
  - [Classes](#classes)
  - [Exceptions](#exceptions)
- [Examples](#examples)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip or uv package manager

### Install from PyPI (when published)

```bash
pip install claude-sdk
```

### Install from source

```bash
# Clone the repository
git clone https://github.com/darinkishore/claude-sdk.git
cd claude-sdk

# Or using uv (recommended)
uv pip install ./python
```

### Development installation

```bash
cd python
pip install maturin
maturin develop
```

## Quick Start

```python
import claude_sdk

# Load a session from a JSONL file
session = claude_sdk.load("~/.claude/projects/myproject/session_20240101_120000.jsonl")

# Basic session info
print(f"Session ID: {session.session_id}")
print(f"Total cost: ${session.total_cost:.4f}")
print(f"Message count: {len(session.messages)}")
print(f"Tools used: {', '.join(session.tools_used)}")

# Iterate through messages
for message in session:
    print(f"{message.role}: {message.text[:100]}...")
    
# Find all your sessions
sessions = claude_sdk.find_sessions()
for session_path in sessions:
    print(f"Found session: {session_path}")
```

## Core Concepts

### Sessions

A **Session** represents a complete conversation with Claude, loaded from a JSONL file. Each session contains:

- Messages exchanged between user and assistant
- Tool executions and their results
- Token usage and cost information
- Conversation structure (including branches and sidechains)
- Metadata and statistics

### Messages

**Messages** are the individual exchanges in a conversation. Each message has:

- `role`: Either "user" or "assistant"
- `text`: The complete text content
- `tools`: List of tools used (if any)
- `cost`: Cost in USD for this specific message
- `timestamp`: When the message was created
- Threading information (`uuid`, `parent_uuid`)

### Projects

A **Project** is a collection of related sessions, typically stored in the same directory. Projects provide aggregate statistics across all sessions.

### Conversation Trees

The SDK automatically reconstructs the conversation structure, handling:

- Linear conversations
- Branching (when you retry or edit messages)
- Sidechains (alternate conversation paths)
- Orphaned messages (missing parents)

## API Reference

### Functions

#### `load(file_path: str | Path) -> Session`

Load a Claude Code session from a JSONL file.

```python
session = claude_sdk.load("path/to/session.jsonl")
```

**Parameters:**
- `file_path`: Path to the JSONL session file

**Returns:** `Session` object

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ParseError`: If the JSONL is malformed
- `ValidationError`: If the session data is invalid

#### `find_sessions(base_path: Optional[str] = None, project: Optional[str] = None) -> List[Path]`

Discover Claude Code session files.

```python
# Find all sessions
all_sessions = claude_sdk.find_sessions()

# Find sessions in a specific project
project_sessions = claude_sdk.find_sessions(project="myproject")

# Search in a custom location
custom_sessions = claude_sdk.find_sessions(base_path="/custom/path")
```

**Parameters:**
- `base_path`: Root directory to search (default: `~/.claude/projects/`)
- `project`: Filter by specific project name

**Returns:** List of `Path` objects to session files

#### `find_projects(base_path: Optional[str] = None) -> List[Path]`

Find all Claude Code projects.

```python
projects = claude_sdk.find_projects()
for project_path in projects:
    print(f"Project: {project_path.name}")
```

**Parameters:**
- `base_path`: Root directory to search (default: `~/.claude/projects/`)

**Returns:** List of `Path` objects to project directories

#### `load_project(project_identifier: str | Path, base_path: Optional[str] = None) -> Project`

Load an entire project with all its sessions.

```python
# Load by project name
project = claude_sdk.load_project("myproject")

# Load by path
project = claude_sdk.load_project("/path/to/project")

print(f"Total sessions: {len(project.sessions)}")
print(f"Total cost: ${project.total_cost:.2f}")
```

**Parameters:**
- `project_identifier`: Project name or path
- `base_path`: Base path for project lookup (if using name)

**Returns:** `Project` object

**Raises:**
- `FileNotFoundError`: If project doesn't exist
- `SessionError`: If no valid sessions found

### Classes

#### Session

Primary container for Claude Code session data.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | Unique session identifier |
| `messages` | `List[Message]` | All messages in conversation order |
| `total_cost` | `float` | Total cost in USD |
| `tools_used` | `List[str]` | Unique tool names used |
| `duration` | `Optional[float]` | Session duration in seconds |
| `conversation_tree` | `ConversationTree` | Message threading structure |
| `metadata` | `SessionMetadata` | Detailed statistics |
| `tool_executions` | `List[ToolExecution]` | All tool runs |
| `tool_costs` | `Dict[str, float]` | Cost breakdown by tool |
| `cost_by_turn` | `List[float]` | Cost per message |
| `project_path` | `Optional[Path]` | Project directory |
| `project_name` | `Optional[str]` | Project name |

**Methods:**

```python
# Get main conversation (excluding sidechains)
main_messages = session.get_main_chain()

# Filter by role
user_messages = session.get_messages_by_role("user")
assistant_messages = session.get_messages_by_role("assistant")

# Find messages using specific tools
bash_messages = session.get_messages_by_tool("bash")

# Get a specific message
message = session.get_message_by_uuid("msg-uuid-123")

# Custom filtering
long_messages = session.filter_messages(lambda m: len(m.text) > 1000)

# Get conversation thread
thread = session.get_thread("msg-uuid-789")  # Returns path from root

# Iteration and length
for msg in session:
    print(msg.text)
    
print(f"Total messages: {len(session)}")
```

#### Message

Represents a single message in the conversation.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `role` | `str` | "user" or "assistant" |
| `text` | `str` | Complete text content |
| `model` | `Optional[str]` | Model used (e.g., "claude-3-sonnet-20240229") |
| `cost` | `Optional[float]` | Cost in USD |
| `tools` | `List[str]` | Tool names used |
| `stop_reason` | `Optional[str]` | Why generation stopped |
| `usage` | `Optional[TokenUsage]` | Token usage details |
| `timestamp` | `str` | RFC3339 timestamp |
| `uuid` | `str` | Unique identifier |
| `parent_uuid` | `Optional[str]` | Parent message UUID |
| `is_sidechain` | `bool` | Whether part of a sidechain |
| `cwd` | `Optional[Path]` | Working directory |
| `total_tokens` | `int` | Total token count |
| `input_tokens` | `int` | Input token count |
| `output_tokens` | `int` | Output token count |

**Methods:**

```python
# Check for tool usage
if message.has_tool_use():
    tools = message.get_tool_blocks()
    for tool in tools:
        print(f"Tool: {tool.name}, Input: {tool.input}")

# Get text content blocks
text_blocks = message.get_text_blocks()

# Get all content blocks with proper typing
for block in message.get_content_blocks():
    if isinstance(block, claude_sdk.TextBlock):
        print(f"Text: {block.text}")
    elif isinstance(block, claude_sdk.ToolUseBlock):
        print(f"Tool: {block.name}")
```

#### Project

Container for multiple sessions in a project.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Project name |
| `sessions` | `List[Session]` | All sessions in project |
| `total_cost` | `float` | Aggregate cost |
| `total_messages` | `int` | Total message count |
| `tool_usage_count` | `Dict[str, int]` | Tool usage frequency |
| `total_duration` | `Optional[float]` | Total time in seconds |

```python
project = claude_sdk.load_project("myproject")

# Analyze tool usage patterns
for tool, count in project.tool_usage_count.items():
    avg_per_session = count / len(project.sessions)
    print(f"{tool}: {count} uses ({avg_per_session:.1f} per session)")

# Find expensive sessions
expensive = [s for s in project.sessions if s.total_cost > 1.0]
```

#### ToolExecution

Complete record of a tool invocation.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `tool_name` | `str` | Name of the tool |
| `input` | `Dict[str, Any]` | Input parameters |
| `output` | `ToolResult` | Execution result |
| `duration_ms` | `Optional[int]` | Execution time |
| `timestamp` | `str` | When executed |

**Methods:**

```python
# Check success
if execution.is_success():
    print(f"{execution.tool_name} completed in {execution.duration_ms}ms")
else:
    print(f"Failed: {execution.output.stderr}")
```

#### ConversationTree

Tree structure representing conversation flow.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `root_messages` | `List[ConversationNode]` | Root nodes |
| `orphaned_messages` | `List[str]` | Messages with missing parents |
| `circular_references` | `List[str]` | Circular reference UUIDs |
| `stats` | `ConversationStats` | Tree statistics |

**Methods:**

```python
tree = session.conversation_tree

# Get tree metrics
print(f"Max depth: {tree.max_depth()}")
print(f"Branch points: {tree.count_branches()}")

# Traverse tree
def walk_tree(node, depth=0):
    print("  " * depth + node.message.text[:50])
    for child in node.children:
        walk_tree(child, depth + 1)

for root in tree.root_messages:
    walk_tree(root)
```

### Exceptions

```python
# Exception hierarchy
claude_sdk.ClaudeSDKError          # Base exception
├── claude_sdk.ParseError          # JSONL parsing failed
├── claude_sdk.ValidationError     # Invalid data
└── claude_sdk.SessionError        # Session-specific issues

# Example handling
try:
    session = claude_sdk.load("session.jsonl")
except claude_sdk.ParseError as e:
    print(f"Failed to parse: {e}")
except claude_sdk.ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

## Examples

### Basic Session Analysis

```python
import claude_sdk

# Load session
session = claude_sdk.load("session.jsonl")

# Print summary
print(f"Session: {session.session_id}")
print(f"Duration: {session.duration / 60:.1f} minutes" if session.duration else "Duration unknown")
print(f"Messages: {len(session)} ({len(session.get_messages_by_role('user'))} from user)")
print(f"Cost: ${session.total_cost:.4f}")
print(f"Tools: {', '.join(session.tools_used) or 'None'}")

# Analyze token usage
total_tokens = sum(msg.total_tokens for msg in session.messages)
print(f"Total tokens: {total_tokens:,}")
```

### Tool Usage Patterns

```python
import claude_sdk
from collections import defaultdict

session = claude_sdk.load("session.jsonl")

# Count tool usage by message
tool_messages = defaultdict(list)
for msg in session.messages:
    if msg.has_tool_use():
        for tool in msg.tools:
            tool_messages[tool].append(msg)

# Print tool usage summary
for tool, messages in sorted(tool_messages.items()):
    print(f"\n{tool}: {len(messages)} uses")
    
    # Show first few uses
    for msg in messages[:3]:
        preview = msg.text[:100].replace('\n', ' ')
        print(f"  - {preview}...")
```

### Cost Analysis Across Projects

```python
import claude_sdk

# Find all projects
projects = claude_sdk.find_projects()

# Analyze costs
project_costs = []
for project_path in projects:
    try:
        project = claude_sdk.load_project(project_path)
        project_costs.append((project.name, project.total_cost, len(project.sessions)))
    except Exception as e:
        print(f"Failed to load {project_path}: {e}")

# Sort by cost
project_costs.sort(key=lambda x: x[1], reverse=True)

# Print report
print("Project Cost Analysis")
print("-" * 50)
for name, cost, session_count in project_costs:
    avg_cost = cost / session_count if session_count > 0 else 0
    print(f"{name:20} ${cost:8.2f} ({session_count:3} sessions, avg ${avg_cost:.2f})")
```

### Conversation Flow Analysis

```python
import claude_sdk

session = claude_sdk.load("session.jsonl")
tree = session.conversation_tree

# Find branching points
for root in tree.root_messages:
    def find_branches(node, path=[]):
        current_path = path + [node.message.uuid]
        
        if len(node.children) > 1:
            print(f"\nBranch point at message {len(current_path)}:")
            print(f"  {node.message.text[:100]}...")
            print(f"  Branches into {len(node.children)} paths")
            
        for child in node.children:
            find_branches(child, current_path)
    
    find_branches(root)

# Analyze sidechains
sidechain_messages = [m for m in session.messages if m.is_sidechain]
if sidechain_messages:
    print(f"\nFound {len(sidechain_messages)} sidechain messages")
```

### Exporting Session Data

```python
import claude_sdk
import json
import csv

session = claude_sdk.load("session.jsonl")

# Export to JSON
export_data = {
    "session_id": session.session_id,
    "total_cost": session.total_cost,
    "messages": [
        {
            "role": msg.role,
            "text": msg.text,
            "cost": msg.cost,
            "timestamp": msg.timestamp,
            "tools": msg.tools
        }
        for msg in session.messages
    ]
}

with open("session_export.json", "w") as f:
    json.dump(export_data, f, indent=2)

# Export tool usage to CSV
with open("tool_usage.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "Tool", "Duration (ms)", "Success"])
    
    for exec in session.tool_executions:
        writer.writerow([
            exec.timestamp,
            exec.tool_name,
            exec.duration_ms or "N/A",
            exec.is_success()
        ])
```

## Performance

The Claude SDK is built with Rust for exceptional performance:

- **Parsing speed**: 1000+ messages per second
- **Memory efficient**: Streaming parser for large files
- **Zero-copy strings**: Minimal memory allocation
- **Thread safe**: Can be used in multi-threaded applications

### Benchmarks

| File Size | Messages | Parse Time | Memory Usage |
|-----------|----------|------------|--------------|
| 100 KB | 50 | <10ms | 2 MB |
| 1 MB | 500 | <50ms | 8 MB |
| 10 MB | 5000 | <300ms | 35 MB |
| 100 MB | 50000 | <3s | 350 MB |

## Troubleshooting

### Common Issues

#### ImportError: No module named 'claude_sdk'

**Solution**: Ensure you've installed the package:
```bash
pip install claude-sdk
# or for development
cd python && maturin develop
```

#### FileNotFoundError when loading sessions

**Solution**: Check the file path and ensure you have read permissions:
```python
import os
path = os.path.expanduser("~/.claude/projects/myproject/session.jsonl")
if os.path.exists(path):
    session = claude_sdk.load(path)
```

#### ParseError: Invalid JSONL format

**Solution**: Ensure the file is a valid Claude Code session file:
```bash
# Check first few lines
head -n 5 session.jsonl

# Validate JSON
python -m json.tool session.jsonl
```

#### High memory usage with large files

**Solution**: Process sessions in batches:
```python
# Instead of loading all sessions at once
sessions = []
for path in claude_sdk.find_sessions(project="large_project"):
    session = claude_sdk.load(path)
    # Process session
    del session  # Free memory
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now SDK operations will print debug info
session = claude_sdk.load("session.jsonl")
```

## Development

### Building from source

```bash
# Clone repository
git clone https://github.com/yourusername/claude-sdk.git
cd claude-sdk

# Build Rust library
cargo build --release

# Build Python package
cd python
maturin build
```

### Running tests

```bash
# Rust tests
cargo test

# Python tests
cd python
maturin develop
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with:
- [PyO3](https://pyo3.rs/) - Rust bindings for Python
- [Maturin](https://maturin.rs/) - Build and publish Rust Python extensions
- [Serde](https://serde.rs/) - Serialization framework for Rust

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/claude-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/claude-sdk/discussions)
- **Documentation**: [Full API Docs](https://yourusername.github.io/claude-sdk/)
