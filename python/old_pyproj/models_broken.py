"""Pydantic data models for Claude Code SDK.

This module provides the foundational type system for parsing Claude Code JSONL session files.
All models are immutable (frozen=True) and use strict validation (extra='forbid').

The models are optimized for memory efficiency and fast performance even with large session files:
- Minimal field footprint and careful type selection
- Memory-efficient container types
- Optimized validation for large message collections
"""

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, PositiveInt

from .utils import decode_project_path, encode_project_path, extract_project_name

# Type aliases for common types
UUIDType = UUID
DateTimeType = datetime
PathType = Path


class UserType(str, Enum):
    """Type of user interaction in Claude Code sessions.

    Determines whether the interaction originated from an external user
    or internal system processes.
    """

    EXTERNAL = "external"  # External user interactions
    INTERNAL = "internal"  # Internal system interactions


class MessageType(str, Enum):
    """Type of message in a conversation.

    Distinguishes between user messages and assistant responses
    in the conversation flow.
    """

    USER = "user"  # User messages
    ASSISTANT = "assistant"  # Assistant responses


class Role(str, Enum):
    """Role in conversation context.

    Defines the role of the message sender in the conversation,
    corresponding to the 'role' field in JSONL records.
    """

    USER = "user"  # User role
    ASSISTANT = "assistant"  # Assistant role


class StopReason(str, Enum):
    """Reason why message generation stopped.

    Indicates the termination condition for assistant message generation,
    providing insight into conversation flow and token usage.
    """

    END_TURN = "end_turn"  # Natural conversation end
    MAX_TOKENS = "max_tokens"  # Token limit reached
    STOP_SEQUENCE = "stop_sequence"  # Stop sequence encountered


class ClaudeSDKBaseModel(BaseModel):
    """Base model class for all Claude SDK Pydantic models.

    Provides consistent configuration across all data models:
    - frozen=True: Makes models immutable after creation
    - extra='forbid': Prevents unexpected fields in input data

    This ensures type safety and catches configuration errors early.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class TextBlock(ClaudeSDKBaseModel):
    """Plain text content block.

    Represents regular text content within messages. This is the most
    common content block type in conversations.
    """

    type: Literal["text"] = "text"
    text: str


class ThinkingBlock(ClaudeSDKBaseModel):
    """Internal thinking/reasoning content block.

    Represents Claude's internal reasoning process that is made visible
    to users. Contains the thinking content and associated signature.
    """

    type: Literal["thinking"] = "thinking"
    thinking: str
    signature: str


class ToolUseBlock(ClaudeSDKBaseModel):
    """Tool usage content block.

    Represents a request to execute a tool with specific parameters.
    Contains tool identification and arbitrary input parameters.
    """

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]


class ToolResultBlock(ClaudeSDKBaseModel):
    """Tool execution result content block.

    Represents the result of a tool execution, including output content,
    error status, and correlation to the original tool use request.
    """

    type: Literal["tool_result"] = "tool_result"
    content: str
    is_error: bool = Field(alias="is_error")
    tool_use_id: str = Field(alias="tool_use_id")


class TokenUsage(ClaudeSDKBaseModel):
    """Token usage statistics for a message.

    Tracks input and output token consumption, including cache usage
    for performance optimization and cost calculation.
    """

    input_tokens: int = Field(ge=0, alias="input_tokens")
    cache_creation_input_tokens: int = Field(default=0, ge=0, alias="cache_creation_input_tokens")
    cache_read_input_tokens: int = Field(default=0, ge=0, alias="cache_read_input_tokens")
    output_tokens: int = Field(ge=0, alias="output_tokens")
    service_tier: str = Field(default="standard", alias="service_tier")


class ToolResult(ClaudeSDKBaseModel):
    """Tool execution result metadata.

    Contains tool execution results as specified in the technical specification,
    including basic execution data and optional metadata.
    """

    tool_use_id: str
    content: str
    stdout: str | None = None
    stderr: str | None = None
    interrupted: bool = False
    is_error: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(ClaudeSDKBaseModel):
    """Message content within a conversation record.

    Represents the actual message data including role, content blocks,
    model information, and token usage statistics.
    """

    id: str | None = None
    role: Role
    model: str | None = None
    content: list["MessageContentBlock"]
    stop_reason: StopReason | None = Field(default=None, alias="stop_reason")
    usage: TokenUsage | None = None


class MessageRecord(ClaudeSDKBaseModel):
    """Complete Claude Code JSONL message record.

    Maps directly to the JSONL structure with conversation threading,
    message content, tool execution results, and performance metrics.
    """

    parent_uuid: UUID | None = Field(default=None, alias="parentUuid")
    is_sidechain: bool = Field(alias="isSidechain")
    user_type: UserType = Field(alias="userType")
    cwd: PathType
    session_id: str = Field(alias="sessionId")
    version: str
    message_type: MessageType = Field(alias="type")
    message: Message
    uuid: UUID
    timestamp: DateTimeType

    # Optional performance and metadata fields
    cost_usd: PositiveFloat | None = Field(default=None, alias="costUSD")
    duration_ms: PositiveInt | None = Field(default=None, alias="durationMs")
    request_id: str | None = Field(default=None, alias="requestId")
    tool_use_result: str | ToolResult | None = Field(default=None, alias="toolUseResult")
    is_meta: bool | None = Field(default=None, alias="isMeta")


class SessionMetadata(ClaudeSDKBaseModel):
    """Session metadata with aggregated cost, token, and tool usage information.

    Aggregates data from all MessageRecords in a session to provide
    session-level analytics and cost tracking.
    """

    total_cost: float = Field(default=0.0, ge=0.0, description="Total USD cost for the session")
    total_messages: int = Field(default=0, ge=0, description="Count of all messages in the session")
    user_messages: int = Field(default=0, ge=0, description="Count of user messages")
    assistant_messages: int = Field(default=0, ge=0, description="Count of assistant messages")

    # Token usage aggregations
    total_input_tokens: int = Field(
        default=0, ge=0, description="Total input tokens across all messages"
    )
    total_output_tokens: int = Field(
        default=0, ge=0, description="Total output tokens across all messages"
    )
    cache_creation_tokens: int = Field(default=0, ge=0, description="Total cache creation tokens")
    cache_read_tokens: int = Field(default=0, ge=0, description="Total cache read tokens")

    # Tool usage tracking
    tool_usage_count: dict[str, int] = Field(
        default_factory=dict, description="Tool name to usage count mapping"
    )
    total_tool_executions: int = Field(
        default=0, ge=0, description="Total number of tool executions"
    )

    # Session timing
    session_start: datetime | None = Field(default=None, description="Timestamp of first message")
    session_end: datetime | None = Field(default=None, description="Timestamp of last message")
    session_duration: timedelta | None = Field(default=None, description="Total session duration")

    # Performance metrics
    average_response_time: float | None = Field(
        default=None, description="Average response time in milliseconds"
    )
    total_duration_ms: int = Field(
        default=0, ge=0, description="Total processing time in milliseconds"
    )


class ToolExecution(ClaudeSDKBaseModel):
    """Tool execution record with timing and result information.

    Represents a single tool execution extracted from tool blocks,
    including input parameters, output results, and performance metrics.
    """

    tool_name: str = Field(description="Name of the executed tool")
    input: dict[str, Any] = Field(description="Tool input parameters")
    output: ToolResult = Field(description="Tool execution output/result")
    duration: timedelta = Field(description="Execution duration")
    timestamp: datetime = Field(description="When the tool was executed")


class ConversationTree(ClaudeSDKBaseModel):
    """Conversation tree structure based on parent_uuid relationships.

    Organizes messages into a tree structure showing conversation branching
    and threading based on parent_uuid relationships.
    """

    root_messages: list[UUID] = Field(
        default_factory=list, description="UUIDs of messages with no parent (conversation roots)"
    )
    parent_to_children: dict[str, list[str]] = Field(
        default_factory=dict, description="Mapping of parent UUID to list of child UUIDs"
    )
    orphaned_messages: list[UUID] = Field(
        default_factory=list, description="Messages with parent_uuid not found in session"
    )
    circular_references: list[tuple[UUID, UUID]] = Field(
        default_factory=list, description="Detected circular parent-child relationships"
    )


class ParsedSession(ClaudeSDKBaseModel):
    """Main session container with messages, metadata, and session information.

    Primary interface for complete session data, aggregating all parsed
    MessageRecords with session-level metadata and analytics.
    """

    session_id: str = Field(description="Unique session identifier")
    messages: list[MessageRecord] = Field(
        default_factory=list, description="All parsed messages in the session"
    )
    summaries: list[str] = Field(default_factory=list, description="Summary records if present")
    conversation_tree: ConversationTree = Field(
        default_factory=ConversationTree,
        description="Conversation tree structure with threading support",
    )
    metadata: SessionMetadata = Field(
        default_factory=SessionMetadata, description="Aggregated session statistics"
    )
    tool_executions: list[ToolExecution] = Field(
        default_factory=list, description="Extracted and correlated tool execution records"
    )

    def validate_session_integrity(self) -> tuple[bool, list[str]]:
        """Validate comprehensive session data integrity.

        Returns:
            tuple: (is_valid, list_of_issues) where is_valid is True if no issues found
        """
        issues: list[str] = []

        # Check if session_id is consistent across all messages
        if self.messages:
            expected_session_id = self.messages[0].session_id
            for i, message in enumerate(self.messages):
                if message.session_id != expected_session_id:
                    issues.append(
                        f"Message {i} has inconsistent session_id: "
                        f"expected {expected_session_id}, got {message.session_id}"
                    )

        # Check metadata consistency
        expected_message_count = len(self.messages)
        if self.metadata.total_messages != expected_message_count:
            issues.append(
                f"Metadata message count mismatch: metadata={self.metadata.total_messages}, "
                f"actual={expected_message_count}"
            )

        # Validate conversation tree integrity
        tree_issues = self._validate_conversation_tree()
        issues.extend(tree_issues)

        # Validate tool execution consistency
        tool_issues = self._validate_tool_executions()
        issues.extend(tool_issues)

        # Validate metadata calculations
        metadata_issues = self._validate_metadata_calculations()
        issues.extend(metadata_issues)

        # Check for duplicate UUIDs
        uuid_issues = self._validate_unique_uuids()
        issues.extend(uuid_issues)

        # Check timestamp ordering
        timestamp_issues = self._validate_timestamp_ordering()
        issues.extend(timestamp_issues)

        return len(issues) == 0, issues

    def _validate_conversation_tree(self) -> list[str]:
        """Validate conversation tree structure."""
        issues: list[str] = []

        if not self.conversation_tree:
            return issues

        # Check for orphaned messages
        if self.conversation_tree.orphaned_messages:
            issues.append(
                f"Found {len(self.conversation_tree.orphaned_messages)} orphaned messages "
                f"with missing parent references"
            )

        # Check for circular references
        if self.conversation_tree.circular_references:
            issues.append(
                f"Found {len(self.conversation_tree.circular_references)} circular references "
                f"in conversation threading"
            )

        # Validate parent-child relationships
        all_message_uuids = {str(msg.uuid) for msg in self.messages}
        for parent_uuid, children in self.conversation_tree.parent_to_children.items():
            if parent_uuid not in all_message_uuids:
                issues.append(f"Parent UUID {parent_uuid} not found in session messages")

            for child_uuid in children:
                if child_uuid not in all_message_uuids:
                    issues.append(f"Child UUID {child_uuid} not found in session messages")

        return issues

    def _validate_tool_executions(self) -> list[str]:
        """Validate tool execution consistency."""
        issues: list[str] = []

        # Check tool execution count matches metadata
        if self.metadata.total_tool_executions != len(self.tool_executions):
            issues.append(
                f"Tool execution count mismatch: metadata={self.metadata.total_tool_executions}, "
                f"actual={len(self.tool_executions)}"
            )

        # Check tool usage count consistency
        tool_count_from_executions: dict[str, int] = {}
        for execution in self.tool_executions:
            tool_count_from_executions[execution.tool_name] = (
                tool_count_from_executions.get(execution.tool_name, 0) + 1
            )

        for tool_name, metadata_count in self.metadata.tool_usage_count.items():
            execution_count = tool_count_from_executions.get(tool_name, 0)
            if metadata_count != execution_count:
                issues.append(
                    f"Tool {tool_name} count mismatch: metadata={metadata_count}, "
                    f"executions={execution_count}"
                )

        return issues

    def _validate_metadata_calculations(self) -> list[str]:
        """Validate metadata calculations against message data."""
        issues: list[str] = []

        # Recalculate metadata and compare
        calculated_metadata = self.calculate_metadata()

        # Compare key metrics
        if abs(self.metadata.total_cost - calculated_metadata.total_cost) > 0.001:
            issues.append(
                f"Total cost mismatch: stored={self.metadata.total_cost}, "
                f"calculated={calculated_metadata.total_cost}"
            )

        if self.metadata.user_messages != calculated_metadata.user_messages:
            issues.append(
                f"User message count mismatch: stored={self.metadata.user_messages}, "
                f"calculated={calculated_metadata.user_messages}"
            )

        if self.metadata.assistant_messages != calculated_metadata.assistant_messages:
            issues.append(
                f"Assistant message count mismatch: stored={self.metadata.assistant_messages}, "
                f"calculated={calculated_metadata.assistant_messages}"
            )

        return issues

    def _validate_unique_uuids(self) -> list[str]:
        """Validate that all message UUIDs are unique."""
        issues: list[str] = []

        uuids = [msg.uuid for msg in self.messages]
        unique_uuids = set(uuids)

        if len(uuids) != len(unique_uuids):
            issues.append(f"Duplicate UUIDs found: {len(uuids)} total, {len(unique_uuids)} unique")

        return issues

    def _validate_timestamp_ordering(self) -> list[str]:
        """Validate that timestamps are in reasonable order."""
        issues: list[str] = []

        if len(self.messages) < 2:
            return issues

        # Check for major timestamp inconsistencies
        sorted_messages = sorted(self.messages, key=lambda m: m.timestamp)

        # Check if session start/end in metadata match actual data
        if (
            self.metadata.session_start
            and sorted_messages
            and self.metadata.session_start != sorted_messages[0].timestamp
        ):
            issues.append(
                f"Session start timestamp mismatch: metadata={self.metadata.session_start}, "
                f"actual={sorted_messages[0].timestamp}"
            )

        if (
            self.metadata.session_end
            and sorted_messages
            and self.metadata.session_end != sorted_messages[-1].timestamp
        ):
            issues.append(
                f"Session end timestamp mismatch: metadata={self.metadata.session_end}, "
                f"actual={sorted_messages[-1].timestamp}"
            )

        return issues

    def calculate_metadata(self) -> SessionMetadata:
        """Calculate comprehensive session metadata from current messages.

        This method is optimized for performance with large message collections:
        - Uses a single pass algorithm to calculate all metrics
        - Avoids redundant iterations over message collection
        - Uses memory-efficient data structures for aggregations

        Returns:
            SessionMetadata: Complete calculated metadata based on current messages
        """
        # Initialize counters
        total_cost = 0.0
        total_messages = len(self.messages)
        user_messages = 0
        assistant_messages = 0

        # Token aggregations
        total_input_tokens = 0
        total_output_tokens = 0
        cache_creation_tokens = 0
        cache_read_tokens = 0

        # Tool usage tracking
        tool_usage_count: dict[str, int] = {}
        total_tool_executions = 0

        # Timing tracking
        session_start: datetime | None = None
        session_end: datetime | None = None
        total_duration_ms = 0
        response_times: list[int] = []

        # Sort messages by timestamp for accurate session timing
        sorted_messages = sorted(self.messages, key=lambda m: m.timestamp)

        for message in sorted_messages:
            # Update session start/end times
            if session_start is None or message.timestamp < session_start:
                session_start = message.timestamp
            if session_end is None or message.timestamp > session_end:
                session_end = message.timestamp

            # Aggregate costs
            if message.cost_usd:
                total_cost += message.cost_usd

            # Count message types
            if message.message.role == Role.USER:
                user_messages += 1
            elif message.message.role == Role.ASSISTANT:
                assistant_messages += 1

            # Aggregate token usage
            if message.message.usage:
                usage = message.message.usage
                total_input_tokens += usage.input_tokens
                total_output_tokens += usage.output_tokens
                cache_creation_tokens += usage.cache_creation_input_tokens
                cache_read_tokens += usage.cache_read_input_tokens

            # Aggregate processing time
            if message.duration_ms:
                total_duration_ms += message.duration_ms
                response_times.append(message.duration_ms)

            # Count tool usage
            for content_block in message.message.content:
                if isinstance(content_block, ToolUseBlock):
                    tool_name = content_block.name
                    tool_usage_count[tool_name] = tool_usage_count.get(tool_name, 0) + 1
                    total_tool_executions += 1

        # Calculate derived metrics
        session_duration = None
        if session_start and session_end:
            session_duration = session_end - session_start

        average_response_time = None
        if response_times:
            average_response_time = sum(response_times) / len(response_times)

        return SessionMetadata(
            total_cost=total_cost,
            total_messages=total_messages,
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
            tool_usage_count=tool_usage_count,
            total_tool_executions=total_tool_executions,
            session_start=session_start,
            session_end=session_end,
            session_duration=session_duration,
            average_response_time=average_response_time,
            total_duration_ms=total_duration_ms,
        )

    def build_conversation_tree(self) -> ConversationTree:
        """Build conversation tree from message parent_uuid relationships.

        This method is optimized for large session files with many messages:
        - Uses efficient dictionary lookups instead of list searches
        - Processes messages in a single pass where possible
        - Avoids redundant data copies during tree construction

        Returns:
            ConversationTree: Complete conversation threading structure
        """
        # Create mapping of UUID to message for quick lookup - O(n) operation
        uuid_to_message = {msg.uuid: msg for msg in self.messages}

        # Track all UUIDs in the session using a set for O(1) lookups
        all_uuids = set(uuid_to_message.keys())

        # Initialize tree structure
        root_messages: list[UUID] = []
        parent_to_children: dict[str, list[str]] = {}
        orphaned_messages: list[UUID] = []
        circular_references: list[tuple[UUID, UUID]] = []

        def check_circular_reference(msg_uuid: UUID) -> bool:
            """Check if this message creates a circular reference."""
            visited: set[UUID] = set()
            current: UUID | None = msg_uuid

            while current is not None:
                if current in visited:
                    return True
                visited.add(current)

                message = uuid_to_message.get(current)
                if not message:
                    break

                current = message.parent_uuid

            return False

        # Process each message to build tree structure
        for message in self.messages:
            msg_uuid = message.uuid
            parent_uuid = message.parent_uuid

            if parent_uuid is None:
                # Root message (no parent)
                root_messages.append(msg_uuid)
            else:
                # Check if parent exists in session
                if parent_uuid not in all_uuids:
                    # Orphaned message - parent not found
                    orphaned_messages.append(msg_uuid)
                else:
                    # Check for circular references
                    if check_circular_reference(msg_uuid):
                        circular_references.append((msg_uuid, parent_uuid))
                    else:
                        # Valid parent-child relationship
                        parent_str = str(parent_uuid)
                        if parent_str not in parent_to_children:
                            parent_to_children[parent_str] = []
                        parent_to_children[parent_str].append(str(msg_uuid))

        return ConversationTree(
            root_messages=root_messages,
            parent_to_children=parent_to_children,
            orphaned_messages=orphaned_messages,
            circular_references=circular_references,
        )

    def extract_tool_executions(self) -> list[ToolExecution]:
        """Extract and correlate tool usage information from message content.

        Returns:
            List of ToolExecution records with correlated input/output pairs
        """
        tool_executions: list[ToolExecution] = []

        # Create mapping of tool_use_id to ToolUseBlock for correlation
        tool_use_blocks: dict[str, tuple[ToolUseBlock, datetime]] = {}

        # First pass: collect all tool use blocks
        for message in self.messages:
            for content_block in message.message.content:
                if isinstance(content_block, ToolUseBlock):
                    tool_use_blocks[content_block.id] = (content_block, message.timestamp)

        # Second pass: find tool results using message-level tool_use_result field
        for message in self.messages:
            if message.tool_use_result and isinstance(message.tool_use_result, ToolResult):
                tool_use_id = message.tool_use_result.tool_use_id

                # Find the corresponding tool use block
                if tool_use_id in tool_use_blocks:
                    tool_use_block, tool_use_timestamp = tool_use_blocks[tool_use_id]

                    # Calculate execution duration - if same message, use message duration
                    if tool_use_timestamp == message.timestamp:
                        execution_duration = (
                            timedelta(milliseconds=message.duration_ms)
                            if message.duration_ms
                            else timedelta(0)
                        )
                    else:
                        execution_duration = message.timestamp - tool_use_timestamp

                    # Create ToolExecution record
                    tool_execution = ToolExecution(
                        tool_name=tool_use_block.name,
                        input=tool_use_block.input,
                        output=message.tool_use_result,
                        duration=execution_duration,
                        timestamp=tool_use_timestamp,
                    )

                    tool_executions.append(tool_execution)

        # Sort by timestamp for consistent ordering
        tool_executions.sort(key=lambda te: te.timestamp)

        return tool_executions

    @classmethod
    def from_message_records(
        cls,
        messages: list[MessageRecord],
        session_id: str | None = None,
        summaries: list[str] | None = None,
    ) -> "ParsedSession":
        """Assemble a complete ParsedSession from MessageRecord list.

        Args:
            messages: List of MessageRecord objects to assemble into a session
            session_id: Override session ID (auto-detected from messages if None)
            summaries: Optional summary records for the session

        Returns:
            ParsedSession: Complete session with threading, metadata, and tool executions

        Raises:
            ValueError: If messages list is empty or session_id cannot be determined
        """
        if not messages:
            raise ValueError("Cannot create ParsedSession from empty message list")

        # Auto-detect session_id if not provided
        if session_id is None:
            session_id = messages[0].session_id

            # Validate all messages have the same session_id
            for message in messages:
                if message.session_id != session_id:
                    raise ValueError(
                        f"Inconsistent session IDs in messages: expected {session_id}, "
                        f"found {message.session_id}"
                    )

        # Create initial ParsedSession with messages
        session = cls(
            session_id=session_id,
            messages=messages,
            summaries=summaries or [],
        )

        # Build conversation tree
        conversation_tree = session.build_conversation_tree()

        # Calculate metadata
        metadata = session.calculate_metadata()

        # Extract tool executions
        tool_executions = session.extract_tool_executions()

        # Return complete assembled session
        return cls(
            session_id=session_id,
            messages=messages,
            summaries=summaries or [],
            conversation_tree=conversation_tree,
            metadata=metadata,
            tool_executions=tool_executions,
        )

    def reconstruct_session(self) -> None:
        """Reconstruct session components from current messages.

        Updates conversation_tree, metadata, and tool_executions in place
        based on current messages list.
        """
        # Note: This would require model reconstruction since models are frozen
        # In practice, use from_message_records() to create a new instance
        raise NotImplementedError(
            "ParsedSession is immutable. Use from_message_records() to create "
            "a new session with updated components."
        )


# Base type alias for content blocks (for isinstance checks)
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


# Type alias for message content (discriminated union - excludes ToolResultBlock per spec)
MessageContentBlock = TextBlock | ThinkingBlock | ToolUseBlock

# Type alias for all content blocks (includes ToolResultBlock)
MessageContentType = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


class Project(ClaudeSDKBaseModel):
    """Project model that aggregates Claude Code sessions within a project directory.

    This model represents a Claude Code project, which is a collection of sessions
    associated with a specific project directory. It provides project-level
    aggregations and utilities for analyzing session data across an entire project.

    Claude Code encodes project paths as directory names in its projects directory:
    - `/Users/darin/Projects/apply-model` → `-Users-darin-Projects-apply-model`
    - `/Users/darin/.claude` → `-Users-darin--claude`

    The Project model provides aggregated analytics including:
    - Total cost across all sessions
    - Tool usage patterns
    - Session counts and temporal distribution

    Attributes:
        project_id: Encoded directory name (e.g., "-Users-darin-Projects-apply-model")
        project_path: Decoded filesystem path (e.g., "/Users/darin/Projects/apply-model")
        name: Display name for the project (e.g., "apply-model")
        sessions: List of Session objects belonging to this project

    Properties:
        total_cost: Sum of session.total_cost across all sessions
        tools_used: Set of tool names used across all sessions
        total_sessions: Number of sessions in the project
        first_session_date: Timestamp of the earliest session
        last_session_date: Timestamp of the most recent session
        total_duration: Total duration from first to last session
    """

    project_id: str = Field(
        description="Encoded directory name (e.g., '-Users-darin-Projects-apply-model')"
    )
    project_path: Path = Field(
        description="Decoded filesystem path (e.g., '/Users/darin/Projects/apply-model')"
    )
    name: str = Field(description="Display name for the project (e.g., 'apply-model')")
    sessions: list["ParsedSession"] = Field(
        default_factory=list, description="Sessions belonging to this project"
    )

    @property
    def total_cost(self) -> float:
        """Total cost of all sessions in the project in USD.

        Aggregates the total_cost of all sessions in the project.

        Returns:
            float: Sum of all session costs
        """
        return sum(session.metadata.total_cost for session in self.sessions)

    @property
    def tools_used(self) -> set[str]:
        """Set of all tool names used across all sessions in the project.

        Returns:
            Set[str]: Union of tools_used across all sessions
        """
        return {tool for session in self.sessions for tool in session.metadata.tool_usage_count}

    @property
    def total_sessions(self) -> int:
        """Number of sessions in the project.

        Returns:
            int: Count of sessions
        """
        return len(self.sessions)

    @property
    def first_session_date(self) -> datetime | None:
        """Timestamp of the earliest session in the project.

        Returns:
            Optional[datetime]: Earliest session timestamp, or None if no sessions
        """
        if not self.sessions:
            return None

        return min(
            (
                session.metadata.session_start
                for session in self.sessions
                if session.metadata.session_start
            ),
            default=None,
        )

    @property
    def last_session_date(self) -> datetime | None:
        """Timestamp of the most recent session in the project.

        Returns:
            Optional[datetime]: Latest session timestamp, or None if no sessions
        """
        if not self.sessions:
            return None

        return max(
            (
                session.metadata.session_end
                for session in self.sessions
                if session.metadata.session_end
            ),
            default=None,
        )

    @property
    def total_duration(self) -> timedelta | None:
        """Total time span from first to last session in the project.

        Returns:
            Optional[timedelta]: Duration from first to last session, or None if insufficient data
        """
        first = self.first_session_date
        last = self.last_session_date

        if first and last:
            return last - first

        return None

    @property
    def tool_usage_count(self) -> dict[str, int]:
        """Aggregated tool usage count across all sessions.

        Returns:
            Dict[str, int]: Mapping of tool names to usage counts
        """
        counts: dict[str, int] = {}

        for session in self.sessions:
            for tool, count in session.metadata.tool_usage_count.items():
                counts[tool] = counts.get(tool, 0) + count

        return counts

    @classmethod
    def from_directory(cls, project_dir: Path) -> "Project":
        """Create a Project from a Claude Code project directory.

        This method scans a Claude Code project directory for session files
        and creates a Project instance containing all sessions found.

        Args:
            project_dir: Path to the Claude Code project directory

        Returns:
            Project: Project instance with all sessions loaded

        Raises:
            ValueError: If the directory doesn't exist or doesn't contain session files
        """
        if not project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")

        if not project_dir.is_dir():
            raise ValueError(f"Not a directory: {project_dir}")

        # Get encoded project ID from directory name
        project_id = encode_project_path(project_dir)

        # Create project without sessions (will add them later)
        project = cls(
            project_id=project_id, project_path=project_dir, name=extract_project_name(project_dir)
        )

        # Load will be implemented later (depends on parser.py)
        # This is a placeholder for the implementation
        # sessions = load_sessions_from_directory(project_dir)
        # project.sessions = sessions

        return project

    @classmethod
    def from_encoded_id(cls, project_id: str) -> "Project":
        """Create a Project from an encoded project ID.

        This method creates a Project instance from an encoded project ID,
        which is the name of the project directory in Claude Code's projects directory.

        Args:
            project_id: Encoded project ID (e.g., "-Users-darin-Projects-apply-model")

        Returns:
            Project: Project instance with the specified project ID

        Raises:
            ValueError: If the project ID is invalid
        """
        # Decode project ID to get filesystem path
        project_path = decode_project_path(project_id)

        # Extract project name
        name = extract_project_name(project_path)

        return cls(project_id=project_id, project_path=project_path, name=name)


# Export all foundation types for public API
__all__ = [
    "ClaudeSDKBaseModel",
    "ContentBlock",
    "ConversationTree",
    "DateTimeType",
    "Message",
    "MessageContentBlock",
    "MessageContentType",
    "MessageRecord",
    "MessageType",
    "ParsedSession",
    "PathType",
    "Project",
    "Role",
    "SessionMetadata",
    "StopReason",
    "TextBlock",
    "ThinkingBlock",
    "TokenUsage",
    "ToolExecution",
    "ToolResult",
    "ToolResultBlock",
    "ToolUseBlock",
    "UUIDType",
    "UserType",
]
