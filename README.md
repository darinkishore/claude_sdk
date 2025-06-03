# claude-sdk

A Rust library with Python bindings for parsing and programmatically controlling Claude Code sessions.

## What is this?

This SDK lets you:
1. **Parse Claude Code sessions** - Extract messages, tool uses, and costs from `.jsonl` files
2. **Control Claude programmatically** - Send prompts, get responses, track file changes
3. **Build automation** - Chain Claude commands together, analyze execution patterns

## Current Status

🟢 **Working Well:**
- Session parsing (reading Claude's JSONL files)
- Basic programmatic control via CLI wrapper
- Cost tracking and analysis
- Python bindings for all core features

🟡 **Experimental:**
- Conversation branching/checkpointing
- Tool permission management
- Session state tracking

🔴 **Not Yet Implemented:**
- DSPy integration modules
- Advanced orchestration patterns
- Streaming responses

## Installation

```bash
pip install claude-sdk
```

Or build from source:
```bash
cd python
pip install maturin
maturin develop
```

## Quick Start

### Parse Claude Sessions

```python
import claude_sdk

# Load a session
session = claude_sdk.load("~/.claude/sessions/session_20250103.jsonl")

# See what happened
print(f"Messages: {len(session.messages)}")
print(f"Total cost: ${session.total_cost():.4f}")

# Find all tool uses
for msg in session.messages:
    for tool in msg.tool_uses:
        print(f"{tool.tool_name}: {tool.input.get('description', '')}")
```

### Control Claude Programmatically

```python
from claude_sdk import ClaudeAgent

# Create an agent in your project directory
agent = ClaudeAgent("/path/to/your/project")

# Send commands
response = agent.send("Fix the failing tests")
print(response.text)
print(f"Files modified: {response.files_modified}")
print(f"Cost: ${response.cost:.4f}")

# Continue the conversation
response = agent.send("Now add documentation")
```

### Analyze Your Claude Usage

```python
# Find all your Claude sessions
sessions = claude_sdk.find_sessions()

# Calculate total costs
total_cost = sum(s.total_cost() for s in sessions)
print(f"Total Claude spend: ${total_cost:.2f}")

# See what tools you use most
from collections import Counter
tool_usage = Counter()
for session in sessions:
    for msg in session.messages:
        for tool in msg.tool_uses:
            tool_usage[tool.tool_name] += 1
```

## Examples

Check out the `python/examples/` directory for more:
- `basic_usage.py` - Simple session parsing
- `analyze_costs.py` - Track your Claude spending
- `conversation_analysis.py` - Analyze conversation patterns
- `tool_usage_analysis.py` - See which tools Claude uses most

## How It Works

Claude Code stores sessions as JSONL files in `~/.claude/`. This SDK:
1. Parses those files to extract all messages and tool uses
2. Wraps the Claude CLI to enable programmatic control
3. Tracks file system changes between commands
4. Provides a clean Python API for it all

## Known Limitations

- Requires Claude Code CLI to be installed for execution features
- Some tool responses appear as "(no content)" when Claude only uses tools
- Session continuations create new session files (by design)
- No Windows support yet (Unix-based systems only)

See [LIMITATIONS.md](LIMITATIONS.md) for the full list.

## Development

See [CLAUDE.md](CLAUDE.md) for development setup and architecture details.

## License

MIT - See [LICENSE](LICENSE) file

## Contributing

Issues and PRs welcome at [github.com/darinkishore/claude_sdk](https://github.com/darinkishore/claude_sdk)

## Related

- [Claude Code](https://claude.ai/code) - The CLI this wraps
- [Anthropic API](https://anthropic.com) - For direct API access