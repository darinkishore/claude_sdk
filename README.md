# Claude SDK 🚀

> **Transform Claude Code from a tool into a programmable AI platform**

[![Rust](https://img.shields.io/badge/rust-1.70%2B-orange.svg)](https://www.rust-lang.org)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

The Claude SDK is a Rust library with Python bindings that unlocks programmatic access to Claude Code. Parse sessions, control Claude programmatically, and build sophisticated AI workflows.

## 🎯 Why Claude SDK?

Ever wanted to:
- 📊 **Analyze your Claude usage** - Track costs, tool patterns, and conversation flows
- 🤖 **Automate Claude workflows** - Build, test, and deploy code programmatically
- 🔍 **Learn from past sessions** - Extract patterns and insights from your Claude history
- 🚀 **Orchestrate complex tasks** - Chain Claude executions with state management

Now you can! The Claude SDK treats Claude as a reliable, tool-using AI primitive that can be orchestrated programmatically.

## 🏗️ Architecture

The SDK is built in four layers:

```
┌─────────────────────────────────────────────────────────┐
│  T3: MCP Support (Future)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │MCP Servers  │  │Tool Perms   │  │ Config Mgmt     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  T2: Git Integration (Coming Soon)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │State Capture│  │Diff Analysis│  │Commit Tracking │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
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

## ⚡ Quick Start

### Installation

```bash
pip install claude-sdk
```

Or build from source:

```bash
git clone https://github.com/yourusername/claude-sdk
cd claude-sdk/python
uv run maturin develop
```

### Your First Script

```python
import claude_sdk

# 1. Analyze past sessions
sessions = claude_sdk.find_sessions()
for session_path in sessions[-5:]:  # Last 5 sessions
    session = claude_sdk.load(session_path)
    print(f"💰 Cost: ${session.total_cost:.4f} | 🛠️ Tools: {', '.join(session.tools_used)}")

# 2. Control Claude programmatically
agent = claude_sdk.ClaudeAgent("/path/to/your/project")
response = agent.send("Add comprehensive error handling to main.py")
print(f"✅ Modified files: {response.files_modified}")
print(f"💵 Cost: ${response.cost:.4f}")
```

## 🌟 Real-World Examples

### 1. Cost Analysis Dashboard

```python
import claude_sdk
from datetime import datetime
from collections import defaultdict

# Analyze monthly Claude costs
monthly_costs = defaultdict(float)
sessions = claude_sdk.find_sessions()

for session_path in sessions:
    session = claude_sdk.load(session_path)
    month = datetime.fromisoformat(session.metadata.timestamp).strftime("%Y-%m")
    monthly_costs[month] += session.total_cost

# Generate report
for month, cost in sorted(monthly_costs.items()):
    print(f"{month}: ${cost:,.2f}")
```

### 2. Automated Code Review

```python
agent = claude_sdk.ClaudeAgent("./my-project")

# Review recent changes
review = agent.send("""
Review the recent changes in this codebase:
1. Check for potential bugs
2. Suggest performance improvements
3. Ensure consistent code style
""")

# Extract specific insights
if "potential bug" in review.text.lower():
    print("⚠️ Potential issues found!")
    
# Save review for team
with open("code-review.md", "w") as f:
    f.write(f"# Code Review - {datetime.now()}\n\n{review.text}")
```

### 3. Test Generation Pipeline

```python
# Generate tests for all Python files
for py_file in Path(".").rglob("*.py"):
    if "test_" not in py_file.name:
        response = agent.send(f"Create comprehensive tests for {py_file}")
        print(f"✅ Generated tests for {py_file.name}")
        
# Run the test suite
result = agent.send("Run all tests and fix any failures")
print(f"📊 Test results: {result.text}")
```

### 4. Learning from Tool Patterns

```python
# Extract tool usage patterns
tool_sequences = []
for session_path in claude_sdk.find_sessions(project="my-project"):
    session = claude_sdk.load(session_path)
    sequence = [exec.tool_name for exec in session.tool_executions]
    tool_sequences.append(sequence)

# Find common patterns
from collections import Counter
common_patterns = Counter(tuple(seq) for seq in tool_sequences if len(seq) > 1)
print("Most common tool sequences:")
for pattern, count in common_patterns.most_common(5):
    print(f"  {' → '.join(pattern)}: {count} times")
```

## 📚 API Reference

### Session Parser (T0)

```python
# Load and analyze sessions
session = claude_sdk.load("path/to/session.jsonl")
sessions = claude_sdk.find_sessions(project="my-project")
project = claude_sdk.load_project("my-project")

# Session properties
session.session_id      # Unique identifier
session.messages        # List of Message objects
session.total_cost      # Total cost in USD
session.duration        # Duration in seconds
session.tools_used      # List of tool names
session.tool_executions # Detailed tool execution data
session.conversation_tree  # Threading structure
```

### Execution Engine (T1)

```python
# High-level API
agent = claude_sdk.ClaudeAgent("/project/path")
response = agent.send("Your prompt here")

# Response properties
response.text           # Claude's response
response.cost           # Cost of this execution
response.files_created  # New files created
response.files_modified # Files that were modified
response.tools_used     # Tools invoked
response.messages       # Full Message objects
response.session_after  # Complete session state

# Low-level API
workspace = claude_sdk.Workspace("/project/path")
conversation = claude_sdk.Conversation(workspace)
transition = conversation.send("Your prompt")

# Transition properties
transition.before       # State before execution
transition.after        # State after execution
transition.execution    # Execution details
transition.tool_executions()  # Extract tool uses
```

### Message Types

```python
# Message structure
message.role      # "user" or "assistant"
message.text      # Message text content
message.cost      # Message cost
message.tools     # Tools used
message.timestamp # ISO timestamp

# Content blocks
blocks = message.get_content_blocks()
for block in blocks:
    if isinstance(block, claude_sdk.TextBlock):
        print(block.text)
    elif isinstance(block, claude_sdk.ToolUseBlock):
        print(f"Tool: {block.name}, ID: {block.id}")
    elif isinstance(block, claude_sdk.ToolResultBlock):
        print(f"Result: {block.content}")
```

## 🛠️ Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-sdk
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

## 🔧 Troubleshooting

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

## 🗺️ Roadmap

### ✅ Completed
- T0: Session parser with full JSONL support
- T1: Execution engine with state tracking
- Python bindings with high/low-level APIs
- Comprehensive test suite

### 🚧 In Progress
- Performance optimizations for large sessions
- Enhanced error recovery

### 📅 Planned 
#### T2: Git Integration
- **State Capture**: Track git state before/after Claude executions
- **Diff Analysis**: Understand exact code changes made by Claude
- **Commit Correlation**: Link commits to specific Claude sessions
- **Branch Awareness**: Support complex git workflows

#### T3: MCP Support
- **Model Context Protocol**: Enable custom tool servers
- **Runtime Management**: Handle MCP server lifecycle
- **Permission System**: Fine-grained tool access control
- **Config Validation**: Compile-time MCP configuration checks

## 🤝 Contributing

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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [PyO3](https://pyo3.rs/) - Rust bindings for Python
- [Maturin](https://maturin.rs/) - Build and publish Rust Python extensions
- [Claude Code](https://claude.ai/code) - The AI platform this SDK orchestrates

---

<p align="center">
  <b>Ready to make Claude programmable?</b><br>
  <a href="#-quick-start">Get Started</a> •
  <a href="https://github.com/darinkishore/claude-sdk/issues">Report Bug</a> •
  <a href="https://github.com/yourusername/claude-sdk/discussions">Join Discussion</a>
</p>
