# Claude SDK

> Rust library with Python bindings for parsing and controlling Claude Code sessions.

[![Rust](https://img.shields.io/badge/rust-1.70%2B-orange.svg)](https://www.rust-lang.org)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Installation

```bash
uv add claude-sdk
```

## Core Concepts

### 1. Sessions
Every Claude execution creates a session containing messages, tool executions, and metadata.

### 2. Agents & Responses  
The `ClaudeAgent` sends prompts and returns `AgentResponse` objects with execution details and full session data.

### 3. Content Blocks
Messages contain typed content blocks: `TextBlock`, `ToolUseBlock`, `ToolResultBlock`.

## Basic Usage

### Simple Command Execution
```python
import claude_sdk

# Create agent for a project directory
agent = claude_sdk.ClaudeAgent("/absolute/path/to/project")

# Send command - returns AgentResponse
response = agent.send("Add type hints to calculator.py")

# Response properties
print(response.text)          # Claude's text response (str | None)
print(response.cost)          # Cost in USD (float)
print(response.session_id)    # Session ID (str)
print(response.files_modified) # List[str] of modified files
print(response.tools_used)    # List[str] of tool names
```

### Accessing Full Session Data
```python
# Every response includes complete session data
response = agent.send("Create a README.md file")
session = response.session_after  # claude_sdk.Session object

# Session properties
print(session.session_id)         # str
print(session.messages)           # List[Message]
print(session.total_cost)         # float (USD)
print(session.tool_executions)    # List[ToolExecution]
print(session.metadata)           # SessionMetadata object
```

### Working with Messages
```python
# Messages have role and content blocks
for message in session.messages:
    print(f"{message.role}: {message.timestamp}")  # role: "user" | "assistant"
    
    # Get typed content blocks
    blocks = message.get_content_blocks()  # List[TextBlock | ToolUseBlock | ToolResultBlock]
    
    for block in blocks:
        if isinstance(block, claude_sdk.TextBlock):
            print(f"  Text: {block.text}")
        elif isinstance(block, claude_sdk.ToolUseBlock):
            print(f"  Tool: {block.name} (id={block.id})")
            print(f"  Input: {block.input}")  # dict
        elif isinstance(block, claude_sdk.ToolResultBlock):
            print(f"  Result for tool_id={block.tool_use_id}")
            print(f"  Content: {block.content}")
```

### Multi-Turn Conversations
```python
# Conversations maintain context automatically
agent = claude_sdk.ClaudeAgent("/path/to/project")

response1 = agent.send("What files are here?")
print(f"Turn 1 cost: ${response1.cost:.4f}")

response2 = agent.send("Add docstrings to the Python files")  
print(f"Turn 2 cost: ${response2.cost:.4f}")
print(f"Total conversation cost: ${agent.total_cost:.4f}")

# Access conversation history
print(f"Total messages: {len(agent.history)}")  # List[AgentResponse]
```

### Tool Execution Details
```python
response = agent.send("Run the test suite and fix any failures")
session = response.session_after

# Detailed tool execution data
for execution in session.tool_executions:
    print(f"Tool: {execution.tool_name}")
    print(f"Success: {execution.is_success()}")  # bool
    print(f"Duration: {execution.duration_ms}ms") # int
    print(f"Output preview: {execution.output.content[:100]}")  # ToolOutput object
```

## Advanced Usage

### Low-Level Control
```python
# Direct workspace and transition control
workspace = claude_sdk.Workspace("/path/to/project")
conversation = claude_sdk.Conversation(workspace, record=True)

# Create prompt with specific session continuation
prompt = claude_sdk.ClaudePrompt(
    text="Continue the refactoring",
    resume_session_id="previous-session-id"  # or None for new session
)

# Send returns Transition object
transition = conversation.send(prompt.text)

# Transition properties
print(transition.before)       # EnvironmentSnapshot
print(transition.after)        # EnvironmentSnapshot  
print(transition.execution)    # ClaudeExecution
print(transition.tools_used()) # List[str]
```

### Session Parsing (T0 API)
```python
# Find and load existing sessions
sessions = claude_sdk.find_sessions()  # List[Path]
session = claude_sdk.load("/path/to/session.jsonl")  # Session object

# Find sessions by project
project_sessions = claude_sdk.find_sessions(project="my-project")
```

### Error Handling
```python
try:
    response = agent.send("Do something")
except claude_sdk.ClaudeSDKError as e:
    print(f"SDK error: {e}")
except claude_sdk.ExecutionError as e:
    print(f"Execution failed: {e}")

## Type Reference

### Core Types
```python
# Main classes
claude_sdk.ClaudeAgent      # High-level conversation interface
claude_sdk.AgentResponse    # Response from agent.send()
claude_sdk.Session          # Parsed session data
claude_sdk.Message          # Individual message
claude_sdk.Workspace        # Low-level workspace
claude_sdk.Conversation     # Low-level conversation
claude_sdk.Transition       # State transition record

# Content blocks
claude_sdk.TextBlock        # Text content
claude_sdk.ToolUseBlock     # Tool invocation
claude_sdk.ToolResultBlock  # Tool result

# Metadata
claude_sdk.SessionMetadata  # Session-level metadata
claude_sdk.ToolExecution    # Detailed tool execution
claude_sdk.EnvironmentSnapshot  # Workspace state

# Exceptions
claude_sdk.ClaudeSDKError   # Base exception
claude_sdk.ParseError       # JSONL parsing failed
claude_sdk.ExecutionError   # Claude execution failed
claude_sdk.ValidationError   # Invalid data
claude_sdk.SessionError     # Session-related error
```

### Key Properties
```python
# AgentResponse
response.text: str | None              # Claude's text response
response.cost: float                   # Cost in USD
response.session_id: str               # Session identifier
response.session_after: Session        # Full session data
response.messages: List[Message]       # Messages from this turn
response.tools_used: List[str]         # Tool names used
response.files_created: List[str]      # Created files
response.files_modified: List[str]     # Modified files
response.duration_ms: int              # Execution time

# Session  
session.session_id: str                # Unique ID
session.messages: List[Message]        # All messages
session.total_cost: float              # Total USD cost
session.tool_executions: List[ToolExecution]  # All tool uses
session.metadata: SessionMetadata      # Session metadata
session.conversation_tree: str | None  # Thread structure
session.cost_by_turn: List[float]      # Cost per turn
session.tools_used: List[str]         # Unique tools used
session.duration: float | None         # Total duration

# Message
message.role: str                      # "user" or "assistant"  
message.timestamp: str                 # ISO timestamp
message.cost: float                    # Message cost
message.get_content_blocks() -> List   # Get typed blocks

# ToolExecution
execution.tool_name: str               # Tool name
execution.is_success() -> bool         # Success status
execution.duration_ms: int             # Execution time
execution.output: ToolOutput           # Tool output
execution.input: dict                  # Tool input parameters

# SessionMetadata
metadata.session_id: str               # Session ID
metadata.timestamp: str                # ISO timestamp
metadata.total_cost_usd: float         # Total cost
metadata.total_duration_ms: int        # Total duration
metadata.total_messages: int           # Message count
metadata.model: str                    # Model used
metadata.tool_stats: dict[str, int]    # Tool usage counts

# ClaudePrompt
prompt.text: str                       # Prompt text
prompt.resume_session_id: str | None   # Session to continue

# Transition
transition.id: str                     # Unique ID
transition.before: EnvironmentSnapshot # Pre-execution state
transition.after: EnvironmentSnapshot  # Post-execution state
transition.execution: ClaudeExecution  # Execution details
transition.tools_used() -> List[str]   # Tools used

# ClaudeExecution
execution.response: str | None         # Text response
execution.cost: float                  # Execution cost
execution.session_id: str              # Session ID
execution.duration_ms: int             # Duration

# EnvironmentSnapshot
snapshot.files: dict[str, FileState]   # File states
snapshot.session_file: Path            # Session JSONL path
snapshot.session_id: str | None        # Session ID
snapshot.timestamp: datetime           # Snapshot time
snapshot.session: Session | None       # Parsed session
```

## Implementation Notes

### Directory Requirements
- Claude CLI requires proper project context
- Cannot execute in arbitrary temp directories
- Use subdirectories of existing projects or user-owned directories

### Path Encoding
Claude uses special path encoding for project directories:
- `/Users/name/.claude/project` → `-Users-name--claude-project`
- Slashes → hyphens
- Dots after slashes → double hyphens
- Underscores → hyphens

### Session Timing
- JSONL files written immediately after execution (microseconds)
- Session costs may show as $0 in parsed JSONL while response.cost is accurate
- Use `response.cost` for accurate per-execution costs

## Architecture

The SDK is built in layers:

```
┌─────────────────────────────────────────────────────────┐
│  T1: Execution Engine ✅                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ClaudeAgent  │  │ Transitions │  │  State Tracking │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  T0: Session Parser ✅                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │JSONL Parser │  │Message Types│  │ Cost Analysis   │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/darinkishore/claude-sdk
cd claude-sdk

# Build Rust library
cargo build --release

# Build Python bindings
cd python
uv run maturin develop

# Run tests
cargo test
uv run pytest tests/
```

### Project Structure

```
claude-sdk/
├── src/                # Rust source code
│   ├── parser/         # T0: JSONL parsing
│   ├── execution/      # T1: Claude control
│   ├── python/         # Python bindings
│   └── types/          # Core data types
├── python/             # Python package
│   ├── claude_sdk/     # Python API
│   └── examples/       # Example scripts
├── tests/              # Test suite
└── ai_docs/            # Architecture docs
```

## Troubleshooting

### Common Issues

**Import Error**: `ImportError: Failed to import Rust core module`
```bash
cd python && uv run maturin develop  # Rebuild bindings
```

**Claude CLI Not Found**: Ensure Claude CLI is installed:
```bash
# Check if installed
which claude

# Install from https://claude.ai/cli
```

**Permission Errors**: The SDK uses `--dangerously-skip-permissions` by default for automation.

### Platform Support

- ✅ macOS (primary development platform)
- ✅ Linux

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork and clone
git clone https://github.com/darinkishore/claude-sdk
cd claude-sdk

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
cargo test
cd python && uv run pytest

# Submit PR
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Important**: Any behavior that doesn't conform to this README should be considered a bug. If you notice any inconsistencies between the documented API and actual behavior, please report it to the human maintaining this SDK.
