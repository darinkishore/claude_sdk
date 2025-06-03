# Claude SDK Python Bindings

Python bindings for the Claude SDK, providing programmatic access to Claude Code sessions and execution.

## Installation

```bash
cd python
pip install -e .
```

Or for development:
```bash
maturin develop
```

## Quick Start

### High-Level API (Recommended)

```python
import claude_sdk

# Create an agent for your project
agent = claude_sdk.ClaudeAgent("/path/to/your/project")

# Send messages naturally
response = agent.send("Create a Python web server with Flask")
print(f"Claude said: {response.text}")
print(f"Cost: ${response.cost:.4f}")
print(f"Files created: {response.files_created}")

# Continue the conversation
response2 = agent.send("Add user authentication")
print(f"Total cost so far: ${agent.total_cost:.4f}")

# Save conversation for later
agent.save_conversation("web_server_session.json")
```

### Low-Level API (Advanced)

```python
import claude_sdk

# Direct control over workspace and conversations
workspace = claude_sdk.Workspace("/path/to/project")
conversation = claude_sdk.Conversation(workspace, record=True)

# Execute and get full transition details
transition = conversation.send("Refactor the authentication module")
print(f"Session ID: {transition.execution.session_id}")
print(f"Tools used: {transition.tools_used()}")
```

## Important Notes

### Directory Requirements

⚠️ **Claude requires a proper project context to work correctly.**

- ✅ **DO**: Test in real project directories or subdirectories
- ❌ **DON'T**: Test in system temp directories (`/tmp`, `/var/folders/...`)

Good testing locations:
- `/your/project/.claude-sdk-test/`
- `~/test-claude-sdk/`
- Any directory within an existing project

### Path Encoding

Claude encodes project paths in a specific way:
- `/Users/name/project` → `-Users-name-project`
- `/Users/name/.hidden` → `-Users-name--hidden`
- `/path/with_underscores` → `-path-with-underscores` (underscores become hyphens!)

## API Overview

### High-Level Classes

**ClaudeAgent** - Simple conversation interface
```python
agent = ClaudeAgent(workspace_path, auto_continue=True)
response = agent.send(message)
agent.save_conversation(path)
```

**AgentResponse** - User-friendly response wrapper
```python
response.text           # Claude's response
response.cost          # Cost in USD
response.files_created # List of created files
response.files_modified # List of modified files
response.tools_used    # Tools Claude used
```

### Low-Level Classes

**Workspace** - Execution environment
```python
workspace = Workspace(path)
snapshot = workspace.snapshot()
```

**Conversation** - Manages execution history
```python
conversation = Conversation(workspace, record=True)
transition = conversation.send(message)
history = conversation.history()
```

**Transition** - Complete state change record
```python
transition.before      # EnvironmentSnapshot before execution
transition.after       # EnvironmentSnapshot after execution
transition.execution   # ClaudeExecution details
transition.tools_used() # List of tools used
```

## Examples

See the `examples/` directory for complete examples:
- `simple_agent_demo.py` - Basic usage of ClaudeAgent
- `test_execution_final.py` - Comprehensive API testing
- `test_agent_api.py` - High-level API features

## Troubleshooting

### "No session files found" Error
This happens when testing in a directory Claude doesn't recognize. Solutions:
1. Use a subdirectory of an existing project
2. Run Claude manually once in the directory to initialize it
3. Ensure the directory is not a system temp directory

### Empty Response Text
Some Claude executions return empty text (e.g., when only using tools). This is normal - check `response.files_modified` to see what changed.

### Import Errors
Run `maturin develop` to rebuild the Python extension after any Rust changes.

## Cost Tracking

The SDK automatically tracks costs:
```python
# Per execution
print(f"This cost: ${response.cost:.4f}")

# Conversation total
print(f"Total cost: ${agent.total_cost:.4f}")
```

## Saving and Loading Conversations

```python
# Save current conversation
agent.save_conversation("session.json")

# Load and continue later
agent = ClaudeAgent.load_conversation("session.json", workspace_path)
agent.send("Continue where we left off")
```