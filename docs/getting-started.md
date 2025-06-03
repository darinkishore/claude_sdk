# Getting Started

## Installation

```bash
pip install claude-sdk
```

## Basic Usage

### 1. Parse a Claude session

```python
import claude_sdk

# Load a session file
session = claude_sdk.load("~/.claude/sessions/session_20250103_123456.jsonl")

# See basic info
print(f"Duration: {session.duration_seconds}s")
print(f"Messages: {len(session.messages)}")
print(f"Cost: ${session.total_cost():.4f}")
```

### 2. Find all your sessions

```python
# Find all Claude sessions on your system
sessions = claude_sdk.find_sessions()

for session in sessions[-5:]:  # Last 5 sessions
    print(f"{session.start_time}: {len(session.messages)} messages, ${session.total_cost():.4f}")
```

### 3. Control Claude programmatically

```python
from claude_sdk import ClaudeAgent

# Point to your project directory
agent = ClaudeAgent("/Users/you/my-project")

# Send a command
response = agent.send("Write a hello world function in main.py")

# See what happened
print(response.text)
print(f"Files created: {response.files_created}")
print(f"Cost: ${response.cost:.4f}")
```

## Next Steps

- Check out the [examples](../python/examples/) directory
- Read the [API Reference](api-reference.md) for all available methods
- See [LIMITATIONS.md](../LIMITATIONS.md) for known issues