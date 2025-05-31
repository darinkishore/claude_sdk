from typing import List, Dict, Optional, Union, Any, Callable, Tuple
from datetime import datetime

# Exception hierarchy
class ClaudeSDKError(Exception):
    """Base class for all Claude SDK exceptions."""
    ...

class ParseError(ClaudeSDKError):
    """Raised when parsing JSONL files fails."""
    ...

class ValidationError(ClaudeSDKError):
    """Raised when validation of data fails."""
    ...

class SessionError(ClaudeSDKError):
    """Raised when session processing fails."""
    ...

# Model classes
class SessionMetadata:
    """Metadata about a parsed session.
    
    This class provides detailed statistics and metadata about a Claude Code session,
    including token usage, timing information, and tool usage patterns.
    """
    total_messages: int
    user_messages: int
    assistant_messages: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    unique_tools_used: List[str]
    total_tool_calls: int
    tool_usage_count: Dict[str, int]
    session_file_path: str
    first_message_timestamp: Optional[str]
    last_message_timestamp: Optional[str]
    session_duration: Optional[int]  # Duration in seconds
    total_duration_ms: int
    average_response_time_ms: Optional[float]

class ToolResult:
    """Result from a tool execution.
    
    Contains the output and status information from a tool invocation.
    """
    tool_use_id: str
    content: str
    stdout: Optional[str]
    stderr: Optional[str]
    interrupted: bool
    is_error: bool
    
    def is_success(self) -> bool:
        """Check if this tool execution was successful."""
        ...
    
    def effective_content(self) -> str:
        """Get the effective output content."""
        ...

class ToolExecution:
    """Represents a complete tool execution with timing.
    
    This class captures a complete tool invocation including input, output, and timing.
    """
    tool_name: str
    input: Dict[str, Any]  # Input parameters as dictionary
    output: ToolResult
    duration_ms: int
    timestamp: str
    
    def is_success(self) -> bool:
        """Check if this tool execution was successful."""
        ...

class ConversationStats:
    """Statistics about a conversation tree.
    
    Provides metrics about the structure of a conversation.
    """
    total_messages: int
    max_depth: int
    num_branches: int
    leaf_count: int

class TextBlock:
    """A block of text content in a message."""
    text: str

class ToolUseBlock:
    """A tool use block in a message.
    
    Represents a tool invocation within a message, including the tool name,
    input parameters, and invocation ID.
    """
    id: str
    name: str
    input: Dict[str, Any]  # Input parameters as dictionary

class Message:
    """Individual message in a Claude Code conversation.
    
    This class represents a single message in a Claude Code conversation,
    with properties for accessing message content, role, cost, and other
    attributes.
    """
    role: str
    text: str
    cost: Optional[float]
    tools: List[str]
    timestamp: str
    uuid: str
    parent_uuid: Optional[str]
    is_sidechain: bool
    cwd: str
    
    def get_tool_blocks(self) -> List[ToolUseBlock]:
        """Get all tool use blocks in this message."""
        ...

class ConversationNode:
    """A node in the conversation tree.
    
    Represents a single message and its children in the conversation tree structure.
    """
    message: Message
    children: List['ConversationNode']
    
    def is_leaf(self) -> bool:
        """Check if this node is a leaf (has no children)."""
        ...
    
    def child_count(self) -> int:
        """Get the number of children."""
        ...

class ConversationTree:
    """Represents a conversation as a tree structure.
    
    This class provides a tree representation of the conversation, showing how messages
    branch and reply to each other. It's useful for analyzing conversation flow and
    finding sidechains or branches.
    """
    root_messages: List[ConversationNode]
    orphaned_messages: List[str]
    circular_references: List[Tuple[str, str]]
    stats: ConversationStats
    
    def max_depth(self) -> int:
        """Get the maximum depth of the conversation tree."""
        ...
    
    def count_branches(self) -> int:
        """Count the number of branching points."""
        ...

class Session:
    """Primary container for Claude Code session data.
    
    This class represents a complete Claude Code session, containing messages,
    conversation threading, tool usage information, and metadata.
    """
    session_id: str
    messages: List[Message]
    total_cost: float
    tools_used: List[str]
    duration: Optional[int]
    conversation_tree: ConversationTree
    metadata: SessionMetadata
    tool_executions: List[ToolExecution]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    message_count: int
    user_message_count: int
    assistant_message_count: int
    root_messages: List[Message]
    conversation_stats: ConversationStats
    tool_costs: Dict[str, float]
    cost_by_turn: List[float]
    project_path: str
    project_name: str
    
    def get_main_chain(self) -> List[Message]:
        """Get only the main conversation chain (excluding sidechains)."""
        ...
    
    def get_messages_by_role(self, role: str) -> List[Message]:
        """Get messages with a specific role."""
        ...
    
    def get_messages_by_tool(self, tool_name: str) -> List[Message]:
        """Get messages that used a specific tool."""
        ...
    
    def get_message_by_uuid(self, uuid: str) -> Optional[Message]:
        """Get a message by its UUID."""
        ...
    
    def filter_messages(self, predicate: Callable[[Message], bool]) -> List[Message]:
        """Filter messages with a custom predicate function."""
        ...
    
    def get_conversation_tree(self) -> ConversationTree:
        """Get the conversation tree structure."""
        ...
    
    def get_thread(self, message_uuid: str) -> List[Message]:
        """Get all messages in a thread from root to specified message."""
        ...
    
    def get_all_threads(self) -> List[List[Message]]:
        """Get all conversation threads."""
        ...
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate various session metrics."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to a dictionary."""
        ...
    
    def __len__(self) -> int: ...
    def __iter__(self) -> 'MessageIterator': ...

class MessageIterator:
    """Iterator for messages in a session."""
    def __iter__(self) -> 'MessageIterator': ...
    def __next__(self) -> Message: ...

class Project:
    """Container for a Claude Code project with multiple sessions.
    
    This class represents a Claude Code project directory containing multiple
    session files. It provides aggregate statistics across all sessions in
    the project.
    """
    name: str
    sessions: List[Session]
    total_cost: float
    total_messages: int
    tool_usage_count: Dict[str, int]
    total_duration: Optional[int]  # Total duration in seconds

# Functions
def load(file_path: Union[str, Any]) -> Session:
    """Load a Claude Code session from a JSONL file.
    
    This function parses a Claude Code session file and returns a Session object
    with all messages, metadata, and tool usage information.
    
    Args:
        file_path: Path to the JSONL session file
    
    Returns:
        Session: Complete session object with messages and metadata
    
    Raises:
        ParseError: If the file cannot be parsed due to invalid format
        FileNotFoundError: If the specified file does not exist
        ClaudeSDKError: Base class for all SDK-specific exceptions
    
    Example:
        >>> from claude_sdk import load
        >>> session = load("conversation.jsonl")
        >>> print(f"Session ID: {session.session_id}")
        >>> print(f"Total cost: ${session.total_cost:.4f}")
    """
    ...

def find_sessions(base_path: Optional[str] = None, project: Optional[str] = None) -> List[str]:
    """Find Claude Code session files.
    
    This function discovers all Claude Code JSONL session files, either in the
    specified base directory or filtered to a specific project.
    
    Args:
        base_path: Directory to search (defaults to ~/.claude/projects/)
        project: Optional project name/path to filter by
    
    Returns:
        List of paths to JSONL session files
    
    Raises:
        ParseError: If the directory doesn't exist or can't be accessed
    """
    ...

def find_projects(base_path: Optional[str] = None) -> List[str]:
    """Find Claude Code project directories.
    
    This function discovers all Claude Code project directories in the specified
    base directory or in the default ~/.claude/projects/ directory.
    
    Args:
        base_path: Directory to search (defaults to ~/.claude/projects/)
    
    Returns:
        List of paths to project directories
    
    Raises:
        ParseError: If the directory doesn't exist or can't be accessed
    """
    ...

def load_project(project_identifier: str, base_path: Optional[str] = None) -> Project:
    """Load a Claude Code project by name or path.
    
    This function loads a Claude Code project, either by name (e.g., 'apply-model')
    or by full path. It discovers all session files in the project directory and
    loads them into a Project object.
    
    Args:
        project_identifier: Project name or full path
        base_path: Base directory to search in (defaults to ~/.claude/projects/)
    
    Returns:
        Project: Project object with all sessions loaded
    
    Raises:
        ParseError: If project cannot be found or sessions cannot be loaded
    """
    ...