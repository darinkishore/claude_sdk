"""Claude SDK - Python wrapper for Claude Code sessions.

This SDK provides a clean interface for parsing and analyzing Claude Code
JSONL session files. It allows you to load session data, access messages, and analyze
costs, tool usage, and conversation patterns.
"""

from pathlib import Path
from typing import Optional, Union, List

# Import from Rust core
try:
    from claude_sdk._core import (
        # Main functions
        load,
        find_sessions as _find_sessions_internal,
        find_projects as _find_projects_internal,
        load_project as _load_project_internal,
        # Classes
        Session,
        Message,
        Project,
        # Model classes
        SessionMetadata,
        ToolResult,
        ToolExecution,
        ConversationStats,
        ConversationNode,
        ConversationTree,
        TextBlock,
        ToolUseBlock,
        ThinkingBlock,
        ImageBlock,
        ToolResultBlock,
        TokenUsage,
        # Execution Engine (T1)
        Workspace,
        Conversation,
        Transition,
        ClaudePrompt,
        ClaudeExecution,
        EnvironmentSnapshot,
        # Exceptions
        ClaudeSDKError,
        ParseError,
        ValidationError,
        SessionError,
    )
except ImportError as e:
    raise ImportError(
        "Failed to import Rust core module. Make sure the package was built with maturin."
    ) from e

__version__ = "0.1.0"

# All classes are now imported from Rust


# The load function is already imported from Rust, no need to redefine it


def find_sessions(
    base_path: Optional[Union[str, Path]] = None,
    project: Optional[Union[str, Path]] = None
) -> List[Path]:
    """Find Claude Code session files.
    
    Args:
        base_path: Directory to search (defaults to ~/.claude/projects/)
        project: Optional project name/path to filter by
        
    Returns:
        List of paths to JSONL session files
    """
    base_path_str = str(base_path) if base_path else None
    project_str = str(project) if project else None
    
    paths = _find_sessions_internal(base_path_str, project_str)
    return [Path(p) for p in paths]


def find_projects(base_path: Optional[Union[str, Path]] = None) -> List[Path]:
    """Find Claude Code project directories.
    
    Args:
        base_path: Directory to search (defaults to ~/.claude/projects/)
        
    Returns:
        List of paths to project directories
    """
    base_path_str = str(base_path) if base_path else None
    paths = _find_projects_internal(base_path_str)
    return [Path(p) for p in paths]


def load_project(
    project_identifier: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None
) -> Project:
    """Load a Claude Code project by name or path.
    
    Args:
        project_identifier: Project name or full path
        base_path: Base directory to search in
        
    Returns:
        Project: Project object with all sessions loaded
    """
    project_str = str(project_identifier)
    base_path_str = str(base_path) if base_path else None
    
    return _load_project_internal(project_str, base_path_str)


# Type exports for static analysis
__all__ = [
    # Error handling
    "ClaudeSDKError",
    "ParseError",
    "ValidationError", 
    "SessionError",
    # Main classes
    "Session",
    "Message",
    "Project",
    # Model classes
    "SessionMetadata",
    "ToolResult",
    "ToolExecution",
    "ConversationStats",
    "ConversationNode",
    "ConversationTree",
    "TextBlock",
    "ToolUseBlock",
    "ThinkingBlock",
    "ImageBlock",
    "ToolResultBlock",
    "TokenUsage",
    # Execution Engine (T1)
    "Workspace",
    "Conversation",
    "Transition",
    "ClaudePrompt",
    "ClaudeExecution",
    "EnvironmentSnapshot",
    # Functions
    "load",
    "find_sessions",
    "find_projects",
    "load_project",
    # Version
    "__version__",
]
