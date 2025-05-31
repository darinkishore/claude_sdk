"""Session container for Claude Code sessions.

This module provides the Session class, which is the primary interface for
working with Claude Code session data. It contains messages, metadata, and
utility methods for analyzing session content, tool usage, and conversation
patterns.

The Session class represents a complete Claude Code conversation, including:
- All messages (user and assistant)
- Tool usage data and costs
- Conversation threading (main chain and sidechains)
- Session metadata (duration, total cost, etc.)
- Project information (project name, path)

Example:
    ```python
    from claude_sdk import load

    # Load a session
    session = load("path/to/session.jsonl")

    # Access key properties
    print(f"Session ID: {session.session_id}")
    print(f"Project: {session.project_name}")
    print(f"Total cost: ${session.total_cost:.4f}")
    print(f"Duration: {session.duration}")
    print(f"Total messages: {len(session.messages)}")
    print(f"Tools used: {', '.join(session.tools_used)}")

    # Filter messages
    user_msgs = session.get_messages_by_role("user")
    main_chain = session.get_main_chain()

    # Analyze costs
    for tool, cost in session.tool_costs.items():
        print(f"{tool}: ${cost:.4f}")
    ```
"""

from datetime import timedelta
from pathlib import Path

from .models import (
    MessageRecord as _MessageRecord,
)
from .models import (
    ParsedSession as _ParsedSession,
)
from .utils import extract_project_name


class Session(_ParsedSession):
    """Primary container for Claude Code session data.

    This class represents a complete Claude Code session, containing messages,
    conversation threading, tool usage information, and metadata. It provides
    properties for common analytics like cost and tool usage, and methods for
    exploring the session content.

    A Session is the central object in the Claude SDK. It contains all the information
    about a Claude Code conversation, including messages, costs, tool usage, and
    conversation structure. The Session class is designed to make it easy to analyze
    Claude Code sessions for cost tracking, tool usage patterns, and conversation flow.

    Args:
        session_id: Unique session identifier
        messages: List of message records from the session
        summaries: Optional summary records for the session
        conversation_tree: Tree structure of message relationships
        metadata: Aggregated session statistics
        tool_executions: Extracted tool execution records

    Properties:
        session_id: Unique identifier for the session
        messages: List of Message objects in conversation order
        total_cost: Total USD cost of the session
        tools_used: Set of tool names used in the session
        duration: Total session duration from first to last message
        tool_costs: Cost breakdown by tool
        cost_by_turn: Cost breakdown by message turn
        conversation_tree: Structure of message relationships
        metadata: Detailed session statistics and counts
        tool_executions: List of detailed tool execution records

    Methods:
        get_main_chain(): Get only the main conversation messages (no sidechains)
        get_messages_by_role(role): Get messages with a specific role (user/assistant)
        from_parsed_session(): Create a Session from a ParsedSession instance
        from_message_records(): Assemble a Session from a list of MessageRecord objects

    Example:
        ```python
        from claude_sdk import load

        # Load a session
        session = load("conversation.jsonl")

        # Basic properties
        print(f"Session ID: {session.session_id}")
        print(f"Total cost: ${session.total_cost:.4f}")
        print(f"Tools used: {session.tools_used}")
        print(f"Messages: {len(session.messages)}")
        print(f"Duration: {session.duration}")

        # Message analysis
        main_chain = session.get_main_chain()  # No sidechains
        user_messages = session.get_messages_by_role("user")
        assistant_messages = session.get_messages_by_role("assistant")

        print(f"Main conversation: {len(main_chain)} messages")
        print(f"User messages: {len(user_messages)}")
        print(f"Assistant messages: {len(assistant_messages)}")

        # Cost analysis
        print("\nTool costs:")
        for tool, cost in sorted(session.tool_costs.items(),
                                key=lambda x: x[1], reverse=True):
            print(f"  {tool}: ${cost:.4f}")

        # Message iteration
        print("\nMessage preview:")
        for i, msg in enumerate(session.messages[:3]):  # First 3 messages
            print(f"{i+1}. {msg.role}: {msg.text[:50]}...")
            if msg.tools:
                print(f"   Tools: {', '.join(msg.tools)}")
        ```

    CLI Usage:
        ```python
        from claude_sdk import load, find_sessions

        # Find and load the most recent session
        paths = find_sessions()
        if paths:
            session = load(paths[0])

            # Quick overview
            print(f"Session from {session.messages[0].timestamp}")
            print(f"Total cost: ${session.total_cost:.4f}")
            print(f"Messages: {len(session.messages)}")
            print(f"Tools: {', '.join(session.tools_used)}")

            # Analyze expensive messages
            print("\nMost expensive messages:")
            for msg in sorted(session.messages,
                             key=lambda m: m.cost or 0, reverse=True)[:3]:
                print(f"${msg.cost:.4f} - {msg.role}: {msg.text[:50]}...")
        ```
    """

    @property
    def total_cost(self) -> float:
        """Total cost of the session in USD.

        This property returns the total cost of the entire session in USD.
        It aggregates costs across all messages and tools used in the session.
        The cost is calculated based on the pricing model for Claude API,
        which includes both input and output tokens.

        Returns:
            float: Total cost in USD

        Example:
            ```python
            session = load("conversation.jsonl")
            print(f"Total session cost: ${session.total_cost:.4f}")
            ```
        """
        return self.metadata.total_cost

    @property
    def tools_used(self) -> set[str]:
        """Set of tool names used in this session.

        This property returns a set containing the names of all tools used
        in this session. Tools are identified by their name (e.g., "Bash",
        "Read", "Write", "Grep"). This is useful for quickly identifying
        which tools were used in a conversation.

        Returns:
            Set[str]: Names of all tools used in the session

        Example:
            ```python
            session = load("conversation.jsonl")
            print(f"Tools used: {', '.join(session.tools_used)}")

            # Check if specific tools were used
            if "Bash" in session.tools_used:
                print("Session used Bash commands")
            ```
        """
        return set(self.metadata.tool_usage_count.keys())

    @property
    def duration(self) -> timedelta | None:
        """Total duration of the session from first to last message.

        This property calculates the time span from the first message to the last
        message in the session. It provides insight into how long the conversation
        took. The duration is returned as a timedelta object, which can be formatted
        as needed.

        Returns None if timestamp information is not available in the session data.

        Returns:
            Optional[timedelta]: Session duration if timestamps available, None otherwise

        Example:
            ```python
            session = load("conversation.jsonl")
            if session.duration:
                hours = session.duration.total_seconds() / 3600
                print(f"Session duration: {hours:.2f} hours")
            else:
                print("Session duration not available")
            ```
        """
        return self.metadata.session_duration

    @property
    def tool_costs(self) -> dict[str, float]:
        """Cost breakdown by tool.

        This property provides a breakdown of costs by tool name. It returns a
        dictionary where keys are tool names and values are the estimated cost
        for that tool's usage across the session. This is useful for analyzing
        which tools contribute most to the total cost.

        The cost distribution is an approximation based on tool usage count
        and the total session cost. It weights each tool's cost by its usage
        frequency.

        Returns:
            Dict[str, float]: Mapping of tool names to their total cost

        Example:
            ```python
            session = load("conversation.jsonl")

            # Print tools from most to least expensive
            for tool, cost in sorted(session.tool_costs.items(),
                                    key=lambda x: x[1], reverse=True):
                print(f"{tool}: ${cost:.4f}")

            # Calculate percentage of cost by tool
            total = session.total_cost
            for tool, cost in session.tool_costs.items():
                percentage = (cost / total * 100) if total else 0
                print(f"{tool}: {percentage:.1f}%")
            ```
        """
        # Use the tool_usage_count from metadata to create dictionary
        tool_costs: dict[str, float] = {}

        # Initialize all tools with 0.0 cost
        for tool_name in self.tools_used:
            tool_costs[tool_name] = 0.0

        # Simple approximation - distribute costs evenly across tools
        if self.tools_used and self.total_cost > 0:
            avg_tool_cost = self.total_cost / len(self.tools_used)
            for tool_name in self.tools_used:
                # Weight by usage count
                usage_count = self.metadata.tool_usage_count.get(tool_name, 0)
                if usage_count > 0:
                    tool_costs[tool_name] = (
                        avg_tool_cost * usage_count / sum(self.metadata.tool_usage_count.values())
                    )

        return tool_costs

    @property
    def cost_by_turn(self) -> list[float]:
        """Cost breakdown by message turn.

        Returns:
            List[float]: List of costs per message, in message order
        """
        return [
            message.cost_usd if message.cost_usd is not None else 0.0 for message in self.messages
        ]

    @classmethod
    def from_parsed_session(cls, parsed_session: _ParsedSession) -> "Session":
        """Create a Session from a ParsedSession instance.

        Args:
            parsed_session: ParsedSession instance to convert

        Returns:
            Session: New Session instance with the same data
        """
        return cls(
            session_id=parsed_session.session_id,
            messages=parsed_session.messages,
            summaries=parsed_session.summaries,
            conversation_tree=parsed_session.conversation_tree,
            metadata=parsed_session.metadata,
            tool_executions=parsed_session.tool_executions,
        )

    @classmethod
    def from_message_records(
        cls,
        messages: list[_MessageRecord],
        session_id: str | None = None,
        summaries: list[str] | None = None,
    ) -> "Session":
        """Assemble a complete Session from MessageRecord list.

        Args:
            messages: List of MessageRecord objects to assemble into a session
            session_id: Override session ID (auto-detected from messages if None)
            summaries: Optional summary records for the session

        Returns:
            Session: Complete session with threading, metadata, and tool executions

        Raises:
            ValueError: If messages list is empty or session_id cannot be determined
        """
        parsed_session = _ParsedSession.from_message_records(
            messages=messages,
            session_id=session_id,
            summaries=summaries,
        )
        return cls.from_parsed_session(parsed_session)

    def get_main_chain(self) -> list[_MessageRecord]:
        """Get only the main conversation chain (excluding sidechains).

        This method filters the session messages to include only those in the main
        conversation thread, excluding any sidechains. Sidechains are parallel
        conversation branches that branch off from the main conversation.

        The main conversation chain represents the primary flow of the conversation
        between the user and assistant, without any parallel threads or explorations.
        This is useful for following the core conversation without distractions.

        Returns:
            List[MessageRecord]: List of messages in the main conversation chain

        Example:
            ```python
            session = load("conversation.jsonl")

            # Get only the main conversation
            main_messages = session.get_main_chain()

            # Compare with total message count
            print(f"Total messages: {len(session.messages)}")
            print(f"Main chain messages: {len(main_messages)}")
            print(f"Sidechain messages: {len(session.messages) - len(main_messages)}")

            # Print the main conversation flow
            for msg in main_messages:
                print(f"{msg.role}: {msg.text[:50]}...")
            ```
        """
        return [msg for msg in self.messages if not msg.is_sidechain]

    def get_messages_by_role(self, role: str) -> list[_MessageRecord]:
        """Get messages with a specific role.

        This method filters the session messages to include only those with
        the specified role. Valid roles are typically "user" or "assistant".
        This is useful for analyzing patterns in user queries or assistant responses.

        Args:
            role: Role to filter by ("user" or "assistant")

        Returns:
            List[MessageRecord]: List of messages with the specified role

        Example:
            ```python
            session = load("conversation.jsonl")

            # Get user and assistant messages separately
            user_messages = session.get_messages_by_role("user")
            assistant_messages = session.get_messages_by_role("assistant")

            # Analyze message patterns
            print(f"User messages: {len(user_messages)}")
            print(f"Assistant messages: {len(assistant_messages)}")

            # Calculate average message length
            avg_user_length = sum(len(msg.text) for msg in user_messages) / len(user_messages)
            avg_assistant_length = sum(len(msg.text) for msg in assistant_messages) / len(assistant_messages)

            print(f"Average user message length: {avg_user_length:.0f} chars")
            print(f"Average assistant message length: {avg_assistant_length:.0f} chars")
            ```
        """
        return [msg for msg in self.messages if msg.message.role == role]

    @property
    def project_path(self) -> Path:
        """Get project filesystem path from session cwd.

        This property returns the filesystem path of the project associated with
        this session, derived from the cwd field of the first message. This path
        can be used to locate related files or to group sessions by project.

        Returns:
            Path: Filesystem path to the project directory

        Raises:
            ValueError: If session has no messages

        Example:
            ```python
            session = load("conversation.jsonl")
            print(f"Project path: {session.project_path}")
            print(f"Project name: {session.project_name}")

            # Group sessions by project
            sessions_by_project = {}
            for path in find_sessions():
                session = load(path)
                project = str(session.project_path)
                if project not in sessions_by_project:
                    sessions_by_project[project] = []
                sessions_by_project[project].append(session)
            ```
        """
        if not self.messages:
            raise ValueError("Cannot determine project path from empty session")
        return self.messages[0].cwd

    @property
    def project_name(self) -> str:
        """Get project display name from session cwd.

        This property returns the display name of the project associated with
        this session, which is the final component of the project path. This
        is useful for grouping sessions by project name in reports and analyses.

        Returns:
            str: Display name for the project (e.g., "apply-model")

        Raises:
            ValueError: If session has no messages

        Example:
            ```python
            session = load("conversation.jsonl")
            print(f"Working in project: {session.project_name}")

            # Filter sessions by project name
            sessions = [load(p) for p in find_sessions()]
            apply_model_sessions = [s for s in sessions if s.project_name == "apply-model"]
            print(f"Found {len(apply_model_sessions)} sessions in 'apply-model' project")
            ```
        """
        return extract_project_name(self.project_path)
