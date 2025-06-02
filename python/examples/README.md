# Claude SDK Python Examples

This directory contains comprehensive examples demonstrating how to use the Claude SDK for Python. Each example is a standalone script that showcases different aspects of the SDK's functionality.

## Examples Overview

### 1. **basic_usage.py** - Getting Started
Learn the fundamentals of using the Claude SDK:
- Loading session files
- Finding sessions and projects
- Iterating through messages
- Accessing basic session properties

```bash
python basic_usage.py
```

### 2. **claude_wrapped.py** - Your Personal Claude Usage Report 🎉
Get a Spotify Wrapped-style analysis of your Claude usage:
- Fun personality insights and achievements
- Cost comparisons ("You spent enough for 52 coffees!")
- Time patterns (are you a night owl?)
- Tool mastery and signature combos
- Memorable moments from your Claude journey

```bash
python claude_wrapped.py
```

### 3. **analyze_costs.py** - Advanced Cost Intelligence 💰
Smart financial insights for your Claude usage:
- Fun comparisons (Netflix subscriptions, daily coffees)
- ROI metrics (cost per problem solved, per code operation)
- Peak spending hours and days visualization
- Cost trends and future projections
- ASCII charts for spending patterns

```bash
python analyze_costs.py
```

### 4. **tool_usage_analysis.py** - Tool Usage Patterns
Deep dive into how tools are used:
- Tool execution statistics (success rates, timing)
- Common tool sequences and combinations
- Tool usage evolution over time
- Performance analysis by tool

```bash
python tool_usage_analysis.py
```

### 4. **conversation_analysis.py** - Conversation Structure
Analyze conversation flow and structure:
- Visualize conversation trees
- Identify branching points and sidechains
- Analyze message threading
- Cross-session pattern discovery

```bash
python conversation_analysis.py
```

### 5. **export_sessions.py** - Data Export
Export session data to various formats:
- JSON (full or summary)
- CSV for spreadsheet analysis
- Markdown for readable documentation
- HTML for interactive viewing
- Project-wide exports

```bash
python export_sessions.py
```

## Prerequisites

Before running these examples, ensure you have:

1. **Claude SDK installed**:
   ```bash
   pip install claude-sdk
   # or for development
   cd ../.. && pip install ./python
   ```

2. **Claude Code sessions** in your system:
   - Default location: `~/.claude/projects/`
   - The SDK will automatically find your sessions

## Running the Examples

Each example can be run independently:

```bash
# Change to examples directory
cd python/examples

# Run any example
python <example_name>.py

# For example:
python basic_usage.py
```

## Understanding the Output

Most examples will:
1. Automatically find your Claude Code sessions
2. Load and analyze the most recent sessions
3. Display results in the terminal
4. Create output files (for export examples)

## Customizing the Examples

Each example includes comments explaining how to modify the code for your needs:

- **Change session paths**: Look for `claude_sdk.load()` calls
- **Adjust analysis parameters**: Modify constants at the top of each file
- **Filter specific projects**: Use the `project` parameter in `find_sessions()`
- **Customize exports**: Modify the export functions to include/exclude data

## Common Patterns

### Loading a Specific Session

```python
import claude_sdk

# Load by exact path
session = claude_sdk.load("/path/to/session.jsonl")

# Load from default location
session = claude_sdk.load("~/.claude/projects/myproject/session_20240101_120000.jsonl")
```

### Finding Sessions

```python
# Find all sessions
all_sessions = claude_sdk.find_sessions()

# Find in specific project
project_sessions = claude_sdk.find_sessions(project="myproject")

# Find with custom base path
custom_sessions = claude_sdk.find_sessions(base_path="/custom/path")
```

### Error Handling

```python
try:
    session = claude_sdk.load("session.jsonl")
except claude_sdk.ParseError as e:
    print(f"Failed to parse: {e}")
except FileNotFoundError:
    print("Session file not found")
except claude_sdk.ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

### Filtering Messages

```python
# By role
user_messages = session.get_messages_by_role("user")

# By tool usage
tool_messages = session.get_messages_by_tool("bash")

# Custom filter
long_messages = session.filter_messages(lambda m: len(m.text) > 1000)
```

## Performance Tips

1. **Process large projects in batches** to manage memory:
   ```python
   for session_path in claude_sdk.find_sessions(project="large_project"):
       session = claude_sdk.load(session_path)
       # Process session
       del session  # Free memory
   ```

2. **Use generators** when possible to avoid loading everything at once

3. **Filter early** to reduce the amount of data processed

## Troubleshooting

If you encounter issues:

1. **No sessions found**: Check that you have Claude Code sessions in `~/.claude/projects/`
2. **Import errors**: Ensure the SDK is properly installed with `pip list | grep claude`
3. **Parse errors**: Verify your JSONL files are valid Claude Code sessions

## Next Steps

After exploring these examples:

1. Check the main [README](../../README.md) for complete API documentation
2. Build your own analysis tools using these examples as templates
3. Contribute your own examples via pull requests

## Support

For issues or questions:
- Check the [SDK documentation](../../README.md)
- Open an issue on GitHub
- Refer to the inline documentation in each example