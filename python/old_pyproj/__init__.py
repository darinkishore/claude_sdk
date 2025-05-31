"""Claude Code SDK - Typed Python wrapper for Claude Code CLI sessions.

This SDK provides a clean, intuitive interface for parsing and analyzing Claude Code
JSONL session files. It allows you to load session data, access messages, and analyze
costs, tool usage, and conversation patterns.

Basic usage:
```python
from claude_sdk import load, Session

# Load a session from a JSONL file
session = load("conversation.jsonl")

# Access session properties
print(f"Session ID: {session.session_id}")
print(f"Total cost: ${session.total_cost:.4f}")
print(f"Tools used: {session.tools_used}")
print(f"Messages: {len(session.messages)}")

# Iterate through messages
for msg in session.messages:
    print(f"{msg.role}: {msg.text}")
    if msg.cost:
        print(f"Cost: ${msg.cost:.4f}")
```

Finding session files:
```python
from claude_sdk import find_sessions

# Find all sessions in ~/.claude/projects/
session_paths = find_sessions()

# Find sessions in a specific directory
session_paths = find_sessions("/path/to/sessions")

# Load and analyze all sessions
for path in session_paths:
    session = load(path)
    print(f"Session {session.session_id}: ${session.total_cost:.4f} USD")
```

Error handling:
```python
from claude_sdk import load, ClaudeSDKError, ParseError

try:
    session = load("conversation.jsonl")
except FileNotFoundError:
    print("Session file not found!")
except ParseError as e:
    print(f"Error parsing session: {e}")
except ClaudeSDKError as e:
    print(f"General SDK error: {e}")
```

Common tool and cost analysis:
```python
from claude_sdk import load

session = load("conversation.jsonl")

# Analyze tool usage
print(f"Tools used: {', '.join(session.tools_used)}")
for tool, cost in session.tool_costs.items():
    print(f"{tool}: ${cost:.4f} USD")

# Find messages using specific tools
for msg in session.messages:
    if "Bash" in msg.tools:
        print(f"Bash command: {msg.text}")
```
"""

from pathlib import Path

from .errors import ClaudeSDKError, ParseError
from .message import Message
from .models import (
    Project,
    Role,
    SessionMetadata,
    TextBlock,
    ThinkingBlock,
    ToolExecution,
    ToolUseBlock,
)
from .parser import (
    find_projects as _find_projects,
)
from .parser import (
    find_sessions as _find_sessions,
)
from .parser import (
    load_project as _load_project,
)
from .parser import (
    parse_complete_session,
)
from .session import Session

__version__ = "1.0.0"


def load(file_path: str | Path) -> Session:
    """Load a Claude Code session from a JSONL file.

    This function parses a Claude Code session file and returns a Session object
    with all messages, metadata, and tool usage information. It handles all the
    complexity of parsing JSONL records, reconstructing the conversation threading,
    and calculating session statistics.

    Args:
        file_path: Path to the JSONL session file (can be string or Path object)
                  This is typically a .jsonl file in ~/.claude/projects/

    Returns:
        Session: Complete session object with the following key properties:
                - session_id: Unique identifier for the session
                - messages: List of Message objects in conversation order
                - total_cost: Total cost of the session in USD
                - tools_used: Set of tool names used in the session
                - duration: Total duration of the session
                - tool_costs: Dictionary mapping tools to their costs
                - cost_by_turn: List of costs per message turn

    Raises:
        ParseError: If the file cannot be parsed due to invalid format or corruption
        FileNotFoundError: If the specified file does not exist
        ClaudeSDKError: Base class for all SDK-specific exceptions
        ValueError: If the file contains invalid or incomplete data

    Example:
        ```python
        from claude_sdk import load

        # Basic usage
        session = load("conversation.jsonl")
        print(f"Session ID: {session.session_id}")
        print(f"Total cost: ${session.total_cost:.4f}")
        print(f"Tools used: {', '.join(session.tools_used)}")

        # Analyze message patterns
        for msg in session.messages:
            print(f"{msg.role}: {msg.text[:50]}...")  # Show message preview
            if msg.tools:
                print(f"  Tools: {', '.join(msg.tools)}")
            if msg.cost:
                print(f"  Cost: ${msg.cost:.4f}")

        # Error handling example
        try:
            session = load("possibly_corrupted.jsonl")
        except ParseError as e:
            print(f"Could not parse file: {e}")
        except FileNotFoundError:
            print("Session file not found!")
        ```

    CLI Usage:
        In Claude Code CLI context, you'll typically use this to load session files:
        ```python
        from claude_sdk import load
        from pathlib import Path

        # For a file you can see in ls output
        session = load("/path/to/your/session.jsonl")

        # With paths from find_sessions()
        session_paths = find_sessions()
        if session_paths:
            session = load(session_paths[0])
        ```
    """
    # Convert string path to Path object if needed
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Parse the session using the internal function
    parsed_session = parse_complete_session(file_path)

    # Convert to the public Session class
    return Session.from_parsed_session(parsed_session)


def find_projects(base_path: str | Path | None = None) -> list[Path]:
    """Find Claude Code project directories.

    This function discovers all Claude Code project directories in the specified
    base directory or in the default ~/.claude/projects/ directory. Project
    directories contain JSONL session files for a specific project.

    Args:
        base_path: Directory to search for project directories. If not provided,
                 defaults to ~/.claude/projects/. Can be a string path or
                 a Path object.

    Returns:
        List[Path]: List of paths to project directories, sorted by modification
                  time (most recent first). The paths are absolute and can be
                  directly passed to the load_project() function.

    Raises:
        ParseError: If the directory doesn't exist or can't be accessed
        FileNotFoundError: If the specified directory does not exist
        PermissionError: If the directory can't be accessed due to permissions

    Example:
        ```python
        from claude_sdk import find_projects, load_project

        # Find all projects
        project_paths = find_projects()
        print(f"Found {len(project_paths)} projects")

        # Show project names
        for path in project_paths[:5]:  # Show 5 most recent
            print(f"Project: {path.name}")

        # Load the most recent project
        if project_paths:
            project = load_project(project_paths[0])
            print(f"Project: {project.name}")
            print(f"Sessions: {len(project.sessions)}")
            print(f"Total cost: ${project.total_cost:.4f}")
        ```

    CLI Usage:
        In Claude Code CLI context, you'll typically use this to find projects:
        ```python
        from claude_sdk import find_projects

        # List available projects
        paths = find_projects()
        for i, path in enumerate(paths[:5]):  # Show 5 most recent
            print(f"{i+1}. {path.name}")

        # Get project names for selection
        project_paths = find_projects()
        project_names = [path.name for path in project_paths]
        print("Available projects:")
        for i, name in enumerate(project_names):
            print(f"{i+1}. {name}")
        ```
    """
    # Convert string path to Path object if needed
    if base_path is not None and isinstance(base_path, str):
        base_path = Path(base_path)

    return _find_projects(base_path)


def load_project(project_identifier: str | Path, base_path: str | Path | None = None) -> Project:
    """Load a Claude Code project by name or path.

    This function loads a Claude Code project, either by name (e.g., 'apply-model')
    or by full path. It discovers all session files in the project directory and
    loads them into a Project object.

    Args:
        project_identifier: Project name (e.g., 'apply-model') or full path
        base_path: Base directory to search in (defaults to ~/.claude/projects/)

    Returns:
        Project: Project object with all sessions loaded

    Raises:
        ParseError: If project cannot be found or sessions cannot be loaded

    Example:
        ```python
        from claude_sdk import load_project

        # Load by project name
        project = load_project("apply-model")
        print(f"Project: {project.name}")
        print(f"Sessions: {len(project.sessions)}")
        print(f"Total cost: ${project.total_cost:.4f}")

        # Load by path
        project = load_project("/Users/username/.claude/projects/-Users-username-Projects-apply-model")

        # Analyze tools used
        for tool, count in project.tool_usage_count.items():
            print(f"{tool}: {count} uses")

        # Get project duration
        if project.total_duration:
            days = project.total_duration.days
            print(f"Project duration: {days} days")
        ```

    CLI Usage:
        In Claude Code CLI context, you'll typically use this to analyze projects:
        ```python
        from claude_sdk import find_projects, load_project

        # Find and load specific project
        paths = find_projects()
        if paths:
            for i, path in enumerate(paths):
                if "apply-model" in str(path):
                    project = load_project(path)
                    print(f"Project: {project.name}")
                    print(f"Sessions: {len(project.sessions)}")
                    print(f"Total cost: ${project.total_cost:.4f}")
                    break
        ```
    """
    # Convert string path to Path object if needed
    if base_path is not None and isinstance(base_path, str):
        base_path = Path(base_path)

    # If project_identifier is a string path, convert to Path
    if isinstance(project_identifier, str) and "/" in project_identifier:
        project_identifier = Path(project_identifier)

    return _load_project(project_identifier, base_path)


def find_sessions(
    base_path: str | Path | None = None, project: str | Path | None = None
) -> list[Path]:
    """Find Claude Code session files, optionally filtered by project.

    This function discovers all Claude Code JSONL session files, either in the
    specified base directory or filtered to a specific project. It enhances the
    existing discover_sessions function with project filtering capabilities.

    Args:
        base_path: Directory to search for session files. If not provided,
                 defaults to ~/.claude/projects/.
        project: Optional project identifier (name or path) to filter sessions by.

    Returns:
        List[Path]: List of paths to JSONL session files, sorted by modification
                  time (most recent first). The paths are absolute and can be
                  directly passed to the load() function.

    Raises:
        ParseError: If the directory doesn't exist or can't be accessed
        FileNotFoundError: If the specified directory does not exist
        PermissionError: If the directory can't be accessed due to permissions

    Example:
        ```python
        from claude_sdk import find_sessions, load, find_projects

        # Basic usage - find all sessions in default directory (~/.claude/projects/)
        session_paths = find_sessions()
        print(f"Found {len(session_paths)} sessions")

        # Find sessions in a specific directory
        session_paths = find_sessions("/path/to/sessions")

        # Find sessions for a specific project
        project_sessions = find_sessions(project="apply-model")
        print(f"Found {len(project_sessions)} sessions in 'apply-model' project")

        # Load the most recent session
        if session_paths:
            latest_session = load(session_paths[0])  # First is most recent
            print(f"Latest session: {latest_session.session_id}")
            print(f"Project: {latest_session.project_name}")
            print(f"Session date: {latest_session.messages[0].timestamp}")

        # Process all sessions in a project
        for path in find_sessions(project="apply-model"):
            try:
                session = load(path)
                print(f"Session {session.session_id}: {len(session.messages)} messages")
            except ParseError:
                print(f"Could not parse {path}")
        ```

    CLI Usage:
        In Claude Code CLI context, you'll typically use this to find sessions:
        ```python
        from claude_sdk import find_sessions, find_projects

        # List recent sessions
        paths = find_sessions()
        for i, path in enumerate(paths[:5]):  # Show 5 most recent
            print(f"{i+1}. {path.name}")

        # Find sessions in specific project
        project_sessions = find_sessions(project="apply-model")
        print(f"Found {len(project_sessions)} sessions in apply-model project")
        ```

    Performance Notes:
        - For large directories with many files, this function is optimized to
          scan quickly using efficient directory traversal.
        - Memory usage is minimized by using generators and lazy evaluation
          for file discovery.
        - The results are cached in memory, so subsequent calls with the same
          base_path will be faster.
        - Using the project filter is much faster than scanning all sessions when
          you only need sessions from a specific project.
    """
    # Convert string path to Path object if needed
    if base_path is not None and isinstance(base_path, str):
        base_path = Path(base_path)

    # If project is a string path, convert to Path
    if isinstance(project, str) and "/" in project:
        project = Path(project)

    return _find_sessions(base_path, project)


# Type exports for static analysis
__all__ = [
    # Error handling
    "ClaudeSDKError",
    "Message",
    "ParseError",
    # Main classes
    "Project",
    # Common model types
    "Role",
    "Session",
    "SessionMetadata",
    "TextBlock",
    "ThinkingBlock",
    "ToolExecution",
    "ToolUseBlock",
    # Version
    "__version__",
    # Project-level functions
    "find_projects",
    # Session-level functions
    "find_sessions",
    "load",
    "load_project",
]
