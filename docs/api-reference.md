# API Reference

## Core Functions

### `load(path: str) -> Session`
Load a Claude session from a JSONL file.

```python
session = claude_sdk.load("~/.claude/sessions/session_20250103.jsonl")
```

### `find_sessions() -> list[Session]`
Find all Claude sessions on your system.

```python
sessions = claude_sdk.find_sessions()
```

### `find_projects() -> list[Project]`
Find all Claude projects (directories with multiple sessions).

```python
projects = claude_sdk.find_projects()
```

### `load_project(name: str) -> Project`
Load a project with all its sessions.

```python
project = claude_sdk.load_project("my-app")
```

## Classes

### `Session`
A parsed Claude session with messages and metadata.

**Properties:**
- `messages: list[Message]` - All messages in the session
- `session_id: str` - Unique session identifier
- `start_time: datetime` - When the session started
- `duration_seconds: float` - How long it lasted
- `model: str` - Claude model used

**Methods:**
- `total_cost() -> float` - Calculate total API cost
- `message_count() -> int` - Number of messages
- `thread_messages() -> ConversationNode` - Build conversation tree

### `Message`
A single message in a Claude conversation.

**Properties:**
- `role: str` - "user" or "assistant"
- `content: str` - Text content
- `tool_uses: list[ToolUse]` - Tools Claude used
- `created_at: datetime` - Timestamp
- `usage: Usage` - Token usage and cost

### `ClaudeAgent`
High-level interface for controlling Claude.

```python
agent = ClaudeAgent(workspace_path: str, auto_continue: bool = True)
```

**Methods:**
- `send(message: str) -> AgentResponse` - Send a message to Claude
- `reset()` - Start a new conversation

### `AgentResponse`
Response from ClaudeAgent.send().

**Properties:**
- `text: str` - Claude's response
- `cost: float` - Cost of this interaction
- `files_created: list[str]` - New files created
- `files_modified: list[str]` - Files that were changed
- `files_deleted: list[str]` - Files that were removed
- `tools_used: list[str]` - Which tools Claude used

## Low-Level Classes

### `Workspace`
Manages execution context.

```python
workspace = Workspace("/path/to/project")
```

### `Conversation`
Manages a sequence of transitions.

```python
conversation = Conversation(workspace)
transition = conversation.send("Do something")
```

### `Transition`
Represents a state change (before → after).

**Properties:**
- `before: EnvironmentSnapshot` - State before execution
- `after: EnvironmentSnapshot` - State after execution
- `prompt: ClaudePrompt` - What was asked
- `execution: ClaudeExecution` - What Claude did

## Exceptions

- `ClaudeSDKError` - Base exception class
- `ParseError` - JSONL parsing failed
- `ValidationError` - Invalid data
- `SessionError` - Session operation failed