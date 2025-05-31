"""Sealed error hierarchy for Claude Code SDK with CLI-friendly error messages."""


class ClaudeSDKError(Exception):
    """Base exception for all Claude SDK errors.

    Provides a common base class for all exceptions raised by the SDK,
    enabling users to catch all SDK-related errors in a single except clause.

    Examples:
        ```python
        try:
            session = load("path/to/session.jsonl")
        except ClaudeSDKError as e:
            print(f"Error: {e}")
            # Take appropriate action based on error
        ```
    """

    def __init__(self, message: str) -> None:
        """Initialize with a clear, actionable error message.

        Args:
            message: Error description with guidance for resolution
        """
        super().__init__(message)


class ParseError(ClaudeSDKError):
    """Exception raised when parsing JSONL session files fails.

    This error includes actionable guidance for resolving common file issues.

    Common causes:
    - File not found or permission denied
    - Invalid JSONL format or corrupted file
    - Directory path issues when searching for sessions

    Examples:
        ```python
        try:
            session = load("nonexistent.jsonl")
        except ParseError as e:
            print(f"Parse error: {e}")
            # e.g. "File not found: nonexistent.jsonl. Check the path and try again."
        ```
    """

    pass


class ValidationError(ClaudeSDKError):
    """Exception raised when data validation fails.

    Provides specific details about what validation failed and how to fix it.

    Common causes:
    - Missing required fields in JSONL records
    - Invalid data types or formats
    - Corrupted or incomplete session data

    Examples:
        ```python
        try:
            session = load("corrupted_session.jsonl")
        except ValidationError as e:
            print(f"Data validation error: {e}")
            # e.g. "Invalid message record at line 42: missing required field 'uuid'"
        ```
    """

    pass


class SessionError(ClaudeSDKError):
    """Exception raised when session processing fails.

    Includes specific information about what went wrong during session reconstruction.

    Common causes:
    - Incomplete conversation threads
    - Missing parent messages
    - Metadata calculation errors

    Examples:
        ```python
        try:
            session = load("broken_threading.jsonl")
        except SessionError as e:
            print(f"Session processing error: {e}")
            # e.g. "Unable to reconstruct conversation: message references missing parent_uuid"
        ```
    """

    pass
