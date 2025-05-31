"""Message class for Claude Code conversations.

This module provides the Message class, which represents individual messages
in a Claude Code conversation, including user inputs and assistant responses.
"""

from .models import (
    MessageRecord as _MessageRecord,
)
from .models import (
    TextBlock,
    ToolUseBlock,
)


class Message(_MessageRecord):
    """Individual message in a Claude Code conversation.

    This class represents a single message in a Claude Code conversation,
    with properties for accessing message content, role, cost, and other
    attributes. It inherits from the internal MessageRecord model but
    provides a simplified interface for common operations.

    The Message class makes it easy to work with individual messages in a Claude Code
    session. Each message has properties for the sender role (user/assistant), text content,
    cost, timestamp, and tools used. Messages also contain information about their position
    in the conversation tree, including parent relationships and sidechain status.

    Args:
        All arguments inherited from the internal MessageRecord class, including:
        - message: The message content and role
        - uuid: Unique message identifier
        - parent_uuid: Parent message UUID for threading
        - timestamp: When the message was sent
        - cost_usd: Cost of the message in USD
        - is_sidechain: Whether this message is part of a sidechain

    Properties:
        role: Role of the message sender ("user" or "assistant")
        text: Text content of the message (concatenated text blocks only)
        cost: Cost of the message in USD
        is_sidechain: Whether this message is part of a sidechain conversation
        timestamp: When the message was sent
        uuid: Unique message identifier
        parent_uuid: Parent message UUID for threading
        tools: List of tool names used in this message
        message: Raw message content (including all content blocks)

    Methods:
        get_tool_blocks(): Get all tool use blocks in this message
        from_message_record(): Create a Message from a MessageRecord instance

    Example:
        ```python
        from claude_sdk import load

        # Basic message iteration
        session = load("conversation.jsonl")
        for message in session.messages:
            print(f"{message.role}: {message.text[:100]}...")
            if message.cost:
                print(f"  Cost: ${message.cost:.4f}")
            if message.is_sidechain:
                print("  (sidechain)")
            if message.tools:
                print(f"  Tools: {', '.join(message.tools)}")

        # Find messages with specific tool usage
        bash_messages = [msg for msg in session.messages if "Bash" in msg.tools]
        for msg in bash_messages:
            print(f"Bash command at {msg.timestamp}")

        # Get all tools used in a specific message
        first_message = session.messages[0]
        tool_blocks = first_message.get_tool_blocks()
        for block in tool_blocks:
            print(f"Used tool: {block.name}")
            print(f"Input: {block.input}")
            print(f"Output: {block.output}")
        ```

    CLI Usage:
        ```python
        from claude_sdk import load, find_sessions
        import datetime

        # Find recent sessions from the last day
        paths = find_sessions()
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

        for path in paths:
            session = load(path)
            # Check first message timestamp
            if session.messages and session.messages[0].timestamp > yesterday:
                print(f"\nSession from {session.messages[0].timestamp}:")
                # Show message summary
                for msg in session.messages:
                    tools_str = f" ({', '.join(msg.tools)})" if msg.tools else ""
                    print(f"- {msg.role}{tools_str}: {msg.text[:50]}...")
        ```
    """

    @property
    def role(self) -> str:
        """Role of the message sender ("user" or "assistant").

        This property returns the role of the message sender, which is typically
        either "user" or "assistant". The role indicates whether the message was
        sent by the human user or by Claude.

        Returns:
            str: Message role ("user" or "assistant")

        Example:
            ```python
            session = load("conversation.jsonl")
            for msg in session.messages:
                if msg.role == "user":
                    print(f"User: {msg.text[:50]}...")
                else:
                    print(f"Assistant: {msg.text[:50]}...")
            ```
        """
        return self.message.role

    @property
    def text(self) -> str:
        """Text content of the message.

        For messages with multiple content blocks, this returns only the text portions
        concatenated together, omitting tool blocks and other non-text content.

        This property provides convenient access to just the human-readable text
        content of the message, filtering out tool blocks and other structured content.
        Text blocks are joined with newlines to preserve paragraph structure.

        Returns:
            str: Text content of the message

        Example:
            ```python
            session = load("conversation.jsonl")

            # Print just the text content from messages
            for msg in session.messages:
                # Limit to first 100 chars for preview
                preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                print(f"{msg.role}: {preview}")

            # Calculate text length statistics
            text_lengths = [len(msg.text) for msg in session.messages]
            avg_length = sum(text_lengths) / len(text_lengths)
            print(f"Average message length: {avg_length:.0f} characters")
            ```
        """
        text_parts: list[str] = []
        for block in self.message.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    @property
    def cost(self) -> float | None:
        """Cost of the message in USD.

        This property returns the cost of this individual message in USD.
        The cost is calculated based on the Claude API pricing model, which
        includes both input and output tokens. For user messages, this typically
        represents input token costs, while for assistant messages it represents
        output token costs.

        Returns None if cost information is not available for this message.

        Returns:
            Optional[float]: Message cost if available, None otherwise

        Example:
            ```python
            session = load("conversation.jsonl")

            # Find the most expensive messages
            expensive_msgs = sorted(
                [m for m in session.messages if m.cost is not None],
                key=lambda m: m.cost or 0,
                reverse=True
            )

            print("Most expensive messages:")
            for msg in expensive_msgs[:3]:  # Top 3
                print(f"${msg.cost:.4f} - {msg.role}: {msg.text[:50]}...")

            # Calculate cost by role
            user_cost = sum(m.cost or 0 for m in session.messages if m.role == "user")
            assistant_cost = sum(m.cost or 0 for m in session.messages if m.role == "assistant")
            print(f"User messages cost: ${user_cost:.4f}")
            print(f"Assistant messages cost: ${assistant_cost:.4f}")
            ```
        """
        return self.cost_usd

    @property
    def tools(self) -> list[str]:
        """List of tools used in this message.

        This property returns a list of tool names used within this message.
        Tools are identified by their name (e.g., "Bash", "Read", "Write").
        This is useful for quickly identifying which tools were used in a
        specific message without diving into the detailed content blocks.

        The list maintains the order in which tools appear in the message.

        Returns:
            List[str]: Names of tools used in this message

        Example:
            ```python
            session = load("conversation.jsonl")

            # Find messages that use the Bash tool
            bash_messages = [msg for msg in session.messages if "Bash" in msg.tools]
            print(f"Found {len(bash_messages)} messages using Bash")

            # Analyze tool usage patterns
            for msg in session.messages:
                if msg.tools:
                    print(f"{msg.role} used: {', '.join(msg.tools)}")

            # Count tool usage frequency
            from collections import Counter
            all_tools = []
            for msg in session.messages:
                all_tools.extend(msg.tools)
            tool_counts = Counter(all_tools)
            print("Tool usage counts:")
            for tool, count in tool_counts.most_common():
                print(f"  {tool}: {count}")
            ```
        """
        tools: list[str] = []
        for block in self.message.content:
            if isinstance(block, ToolUseBlock):
                tools.append(block.name)
        return tools

    @classmethod
    def from_message_record(cls, record: _MessageRecord) -> "Message":
        """Create a Message from a MessageRecord instance.

        Args:
            record: MessageRecord instance to convert

        Returns:
            Message: New Message instance with the same data
        """
        # Convert using model_dump and model_validate to preserve all data
        return cls.model_validate(record.model_dump())

    def get_tool_blocks(self) -> list[ToolUseBlock]:
        """Get all tool use blocks in this message.

        This method returns a list of all ToolUseBlock objects contained in this message.
        Each ToolUseBlock represents a tool invocation, including the tool name, input,
        and output. This provides detailed access to tool usage information beyond
        just the tool names.

        ToolUseBlocks contain the complete record of tool invocations, including:
        - tool name (e.g., "Bash", "Read")
        - input parameters (e.g., command text, file path)
        - output results (text output, error information)
        - execution status

        This is useful for detailed analysis of tool usage patterns and extracting
        specific command inputs and outputs.

        Returns:
            List[ToolUseBlock]: List of tool use blocks in this message

        Example:
            ```python
            session = load("conversation.jsonl")

            # Find all Bash commands in the session
            bash_commands = []
            for msg in session.messages:
                tool_blocks = msg.get_tool_blocks()
                for block in tool_blocks:
                    if block.name == "Bash":
                        # Extract the command from the input
                        if hasattr(block.input, "command"):
                            bash_commands.append(block.input.command)

            print(f"Found {len(bash_commands)} Bash commands:")
            for i, cmd in enumerate(bash_commands[:5], 1):  # Show first 5
                print(f"{i}. {cmd}")

            # Analyze tool success/failure patterns
            success_count = 0
            error_count = 0

            for msg in session.messages:
                for block in msg.get_tool_blocks():
                    if hasattr(block.output, "is_error") and block.output.is_error:
                        error_count += 1
                    else:
                        success_count += 1

            total = success_count + error_count
            if total > 0:
                success_rate = (success_count / total) * 100
                print(f"Tool success rate: {success_rate:.1f}%")
            ```
        """
        return [block for block in self.message.content if isinstance(block, ToolUseBlock)]
