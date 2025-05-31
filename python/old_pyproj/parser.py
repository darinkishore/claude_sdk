"""JSONL parsing and session reconstruction for Claude Code SDK."""

import json
import logging
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from .errors import ParseError
from .models import MessageRecord, ParsedSession, Project
from .utils import decode_project_path

logger = logging.getLogger(__name__)


def find_projects(base_path: Path | None = None) -> list[Path]:
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
    """
    if base_path is None:
        base_path = Path.home() / ".claude" / "projects"

    if not base_path.exists():
        raise ParseError(
            f"Projects directory not found: {base_path}. Please verify the directory exists or specify a different path."
        )

    if not base_path.is_dir():
        raise ParseError(
            f"Projects path is not a directory: {base_path}. Please specify a valid directory path."
        )

    try:
        # Find all directories that might be project directories
        # Only include directories that start with "-" (Claude Code encoding)
        project_dirs = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("-")]

        # Sort by modification time (most recent first)
        project_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

        logger.info(f"Found {len(project_dirs)} potential project directories in {base_path}")
        return project_dirs
    except (OSError, PermissionError) as e:
        raise ParseError(
            f"Failed to access projects directory {base_path}: {e}. Check permissions and try again."
        ) from e


def discover_sessions(base_path: Path | None = None) -> list[Path]:
    """Discover Claude Code session files in the user's projects directory.

    Args:
        base_path: Base directory to search. Defaults to ~/.claude/projects/

    Returns:
        List of paths to JSONL session files

    Raises:
        ParseError: If base directory doesn't exist or isn't accessible
    """
    if base_path is None:
        base_path = Path.home() / ".claude" / "projects"

    if not base_path.exists():
        raise ParseError(
            f"Projects directory not found: {base_path}. Please verify the directory exists or specify a different path."
        )

    if not base_path.is_dir():
        raise ParseError(
            f"Projects path is not a directory: {base_path}. Please specify a valid directory path."
        )

    try:
        # Find all .jsonl files recursively
        session_files = list(base_path.rglob("*.jsonl"))
        logger.info(f"Found {len(session_files)} JSONL files in {base_path}")

        # Sort by modification time (most recent first)
        session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        return session_files
    except (OSError, PermissionError) as e:
        raise ParseError(
            f"Failed to access projects directory {base_path}: {e}. Check permissions and try again."
        ) from e


def parse_jsonl_file(file_path: Path) -> Iterator[MessageRecord]:
    """Parse a JSONL file line-by-line into MessageRecord objects.

    This function uses a memory-efficient streaming approach to process even large session
    files without loading the entire file into memory. Invalid lines are logged and skipped.

    Args:
        file_path: Path to the JSONL file to parse

    Yields:
        MessageRecord objects for each valid line

    Raises:
        ParseError: If file cannot be opened or read
    """
    if not file_path.exists():
        raise ParseError(
            f"Session file not found: {file_path}. Please check that the file exists and the path is correct."
        )

    if not file_path.is_file():
        raise ParseError(
            f"Session path is not a file: {file_path}. Please provide a path to a valid JSONL file."
        )

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                try:
                    # Parse JSON line
                    json_data = json.loads(line)

                    # Convert to MessageRecord using Pydantic
                    message_record = MessageRecord.model_validate(json_data)
                    yield message_record

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at {file_path}:{line_num}: {e}")
                    # Record more specific error information
                    logger.debug(f"Problematic line content: {line[:100]}...")
                    continue  # Skip malformed JSON lines

                except ValidationError as e:
                    # Convert Pydantic validation error to our custom error with better message
                    logger.warning(f"Data validation error at {file_path}:{line_num}: {e}")
                    # Extract field names for better debugging
                    error_fields = [str(err["loc"][0]) for err in e.errors()]
                    logger.debug(f"Invalid fields: {', '.join(error_fields)}")
                    continue  # Skip lines that don't match MessageRecord schema

                except Exception as e:
                    logger.error(f"Unexpected error at {file_path}:{line_num}: {e}")
                    continue  # Continue processing despite unexpected errors

    except (OSError, PermissionError) as e:
        # Provide actionable error message based on error type
        if isinstance(e, PermissionError):
            raise ParseError(
                f"Permission denied when reading {file_path}: {e}. "
                f"Check file permissions and try again."
            ) from e
        else:
            raise ParseError(
                f"Failed to read session file {file_path}: {e}. "
                f"Verify the file is accessible and not corrupted."
            ) from e


def parse_session_file(file_path: Path) -> list[MessageRecord]:
    """Parse a complete JSONL session file into a list of MessageRecord objects.

    This function optimizes memory usage for large files by using a streaming parser
    and only materializing the list at the end of processing.

    Args:
        file_path: Path to the JSONL session file

    Returns:
        List of MessageRecord objects from the session

    Raises:
        ParseError: If file cannot be parsed
    """
    try:
        records = list(parse_jsonl_file(file_path))
        logger.info(f"Successfully parsed {len(records)} records from {file_path}")
        return records
    except ParseError:
        raise  # Re-raise ParseError as-is
    except Exception as e:
        # Provide more context and suggestions in the error message
        raise ParseError(
            f"Failed to parse session file {file_path}: {e}. "
            f"The file may be corrupted or in an unexpected format. "
            f"Try running 'just check' to validate your environment."
        ) from e


class SessionParser:
    """High-level parser for Claude Code session files.

    Provides methods for discovering and parsing JSONL session files
    with comprehensive error handling and logging.
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize the session parser.

        Args:
            base_path: Base directory for session discovery. Defaults to ~/.claude/projects/
        """
        self.base_path = base_path or Path.home() / ".claude" / "projects"

    def discover_sessions(self) -> list[Path]:
        """Discover all JSONL session files in the base path.

        Returns:
            List of paths to discovered session files
        """
        return discover_sessions(self.base_path)

    def parse_session(self, file_path: Path) -> list[MessageRecord]:
        """Parse a single JSONL session file.

        Args:
            file_path: Path to the session file

        Returns:
            List of MessageRecord objects from the session
        """
        return parse_session_file(file_path)

    def parse_all_sessions(self) -> dict[Path, list[MessageRecord]]:
        """Parse all discovered session files.

        Returns:
            Dictionary mapping file paths to lists of MessageRecord objects
        """
        session_files = self.discover_sessions()
        results: dict[Path, list[MessageRecord]] = {}

        for file_path in session_files:
            try:
                records = self.parse_session(file_path)
                results[file_path] = records
            except ParseError as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                results[file_path] = []  # Empty list for failed sessions

        return results

    def parse_complete_session(self, file_path: Path) -> ParsedSession:
        """Parse a single JSONL session file into a complete ParsedSession.

        Args:
            file_path: Path to the session file

        Returns:
            ParsedSession: Complete session with threading, metadata, and tool executions
        """
        return parse_complete_session(file_path)


def resolve_project_path(project_identifier: str | Path, base_path: Path | None = None) -> Path:
    """Resolve project identifier to a project directory path.

    This function resolves a project identifier (either a name like 'apply-model'
    or a full path) to the actual project directory path in the Claude Code
    projects directory structure.

    Args:
        project_identifier: Project name or full path
        base_path: Base directory to search in (defaults to ~/.claude/projects/)

    Returns:
        Path: Resolved project directory path

    Raises:
        ParseError: If project cannot be found or multiple matches exist
    """
    if base_path is None:
        base_path = Path.home() / ".claude" / "projects"

    # If identifier is already a Path, check if it exists
    if isinstance(project_identifier, Path):
        if not project_identifier.exists():
            raise ParseError(f"Project directory not found: {project_identifier}")
        if not project_identifier.is_dir():
            raise ParseError(f"Not a directory: {project_identifier}")
        return project_identifier

    # Handle string identifier (project name)
    # First check if it's an encoded directory name itself
    if project_identifier.startswith("-"):
        potential_path = base_path / project_identifier
        if potential_path.exists() and potential_path.is_dir():
            return potential_path

    # Search for matching project by name
    matches: list[Path] = []
    for project_dir in base_path.iterdir():
        if not project_dir.is_dir():
            continue

        # Try to decode the directory name and match with the project name
        try:
            if project_dir.name.startswith("-"):  # Only process encoded paths
                decoded_path = decode_project_path(project_dir.name)
                if decoded_path.name == project_identifier:
                    matches.append(project_dir)
        except ValueError:
            # Skip directories with invalid encoding
            continue

    # Check match count
    if not matches:
        raise ParseError(
            f"Project '{project_identifier}' not found. Use find_projects() to see available projects."
        )

    if len(matches) > 1:
        match_names = [m.name for m in matches]
        raise ParseError(
            f"Multiple projects matched '{project_identifier}': {match_names}. "
            f"Please specify a full path to disambiguate."
        )

    return matches[0]


def load_project(project_identifier: str | Path, base_path: Path | None = None) -> Project:
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
    """
    # Resolve project path
    project_dir = resolve_project_path(project_identifier, base_path)

    # Create Project object using from_directory
    project = Project.from_directory(project_dir)

    # Find all session files in the project directory
    try:
        session_files = list(project_dir.glob("*.jsonl"))
        session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        logger.info(f"Found {len(session_files)} session files in project '{project.name}'")

        # Load each session
        sessions: list[ParsedSession] = []
        for file_path in session_files:
            try:
                session = parse_complete_session(file_path)
                sessions.append(session)
            except ParseError as e:
                logger.warning(f"Skipping session file {file_path}: {e}")

        # Update project with loaded sessions
        # We can't directly modify the project.sessions attribute because Project is immutable
        # We have to create a new Project instance with the loaded sessions
        project = Project(
            project_id=project.project_id,
            project_path=project.project_path,
            name=project.name,
            sessions=sessions,
        )

        logger.info(f"Loaded {len(sessions)} sessions for project '{project.name}'")
        return project

    except Exception as e:
        raise ParseError(
            f"Failed to load project '{project_identifier}': {e}. "
            f"Check that the project directory exists and contains valid session files."
        ) from e


def find_sessions(base_path: Path | None = None, project: str | Path | None = None) -> list[Path]:
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
                  time (most recent first).

    Raises:
        ParseError: If directories don't exist or can't be accessed
    """
    if project is None:
        # Use original discover_sessions behavior
        return discover_sessions(base_path)

    # Get default base path if not provided
    if base_path is None:
        base_path = Path.home() / ".claude" / "projects"

    # Resolve project directory
    try:
        project_dir = resolve_project_path(project, base_path)

        # Find all session files in the project directory
        session_files = list(project_dir.glob("*.jsonl"))
        session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        logger.info(f"Found {len(session_files)} session files in project directory {project_dir}")
        return session_files

    except ParseError:
        # Re-raise original error
        raise
    except Exception as e:
        raise ParseError(
            f"Failed to find sessions for project '{project}': {e}. "
            f"Check that the project exists and is accessible."
        ) from e


def parse_complete_session(file_path: Path) -> ParsedSession:
    """Parse a JSONL session file into a complete ParsedSession with threading and metadata.

    This function optimizes performance for large session files by:
    1. Using memory-efficient streaming for initial parsing
    2. Processing messages in batches for threading reconstruction
    3. Calculating metadata incrementally to avoid redundant processing

    Args:
        file_path: Path to the JSONL session file

    Returns:
        ParsedSession: Complete session with conversation threading, metadata, and tool executions

    Raises:
        ParseError: If file cannot be parsed
    """
    try:
        # Parse raw message records
        message_records = parse_session_file(file_path)

        # Assemble into complete ParsedSession
        session = ParsedSession.from_message_records(message_records)

        logger.info(
            f"Successfully parsed session {session.session_id} with "
            f"{len(session.messages)} messages, "
            f"{len(session.tool_executions)} tool executions"
        )

        return session

    except ParseError:
        raise  # Re-raise ParseError as-is
    except Exception as e:
        # Check for common error types and provide specific guidance
        if "session_id" in str(e):
            raise ParseError(
                f"Failed to process session from {file_path}: Missing or invalid session_id. "
                f"The file may not be a valid Claude Code session file."
            ) from e
        elif "threading" in str(e).lower() or "parent" in str(e).lower():
            raise ParseError(
                f"Failed to reconstruct conversation threading from {file_path}: {e}. "
                f"The session file may contain incomplete message chains."
            ) from e
        else:
            raise ParseError(
                f"Failed to parse complete session from {file_path}: {e}. "
                f"Try using parse_session_file() to access raw messages without reconstruction."
            ) from e
