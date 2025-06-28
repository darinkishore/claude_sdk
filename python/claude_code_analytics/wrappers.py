"""Typed Python wrappers for the Rust extension module.

These classes mirror the structures provided by ``_core`` but expose
Python type hints for better IDE support. For usage examples, refer to
the ``API Reference`` section of the project's README.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from . import _core


class _WrapperBase:
    """Base class that delegates attribute access to an internal object."""

    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def __repr__(self) -> str:  # pragma: no cover - delegate repr
        return repr(self._inner)


# Content block wrappers ----------------------------------------------------

@dataclass
class TextBlock(_WrapperBase):
    """Plain text content block."""

    _inner: _core.TextBlock

    @property
    def text(self) -> str:
        return self._inner.text


@dataclass
class ToolUseBlock(_WrapperBase):
    """Block describing a tool invocation."""

    _inner: _core.ToolUseBlock

    @property
    def id(self) -> str:
        return self._inner.id

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def input(self) -> dict:
        return self._inner.input


@dataclass
class ThinkingBlock(_WrapperBase):
    """Block representing assistant reasoning."""

    _inner: _core.ThinkingBlock

    @property
    def signature(self) -> str:
        return self._inner.signature

    @property
    def thinking(self) -> str:
        return self._inner.thinking


@dataclass
class ImageBlock(_WrapperBase):
    """Image data block."""

    _inner: _core.ImageBlock

    @property
    def data(self) -> str:
        return self._inner.data

    @property
    def media_type(self) -> str:
        return self._inner.media_type

    @property
    def source_type(self) -> str:
        return self._inner.source_type


@dataclass
class ToolResultBlock(_WrapperBase):
    """Result block produced by a tool call."""

    _inner: _core.ToolResultBlock

    @property
    def tool_use_id(self) -> str:
        return self._inner.tool_use_id

    @property
    def content(self) -> str:
        return self._inner.content

    @property
    def is_error(self) -> bool:
        return self._inner.is_error


ContentBlock = Union[TextBlock, ToolUseBlock, ThinkingBlock, ImageBlock, ToolResultBlock]


# Token usage ---------------------------------------------------------------

@dataclass
class TokenUsage(_WrapperBase):
    """Token counts returned by the API."""

    _inner: _core.TokenUsage

    @property
    def input_tokens(self) -> int:
        return self._inner.input_tokens

    @property
    def output_tokens(self) -> int:
        return self._inner.output_tokens

    @property
    def service_tier(self) -> Optional[str]:
        return self._inner.service_tier

    @property
    def cache_creation_input_tokens(self) -> int:
        return self._inner.cache_creation_input_tokens

    @property
    def cache_read_input_tokens(self) -> int:
        return self._inner.cache_read_input_tokens


# Tool result and execution -------------------------------------------------

@dataclass
class ToolResult(_WrapperBase):
    """Output from a tool execution."""

    _inner: _core.ToolResult

    @property
    def tool_use_id(self) -> str:
        return self._inner.tool_use_id

    @property
    def content(self) -> str:
        return self._inner.content

    @property
    def stdout(self) -> Optional[str]:
        return self._inner.stdout

    @property
    def stderr(self) -> Optional[str]:
        return self._inner.stderr

    @property
    def interrupted(self) -> bool:
        return self._inner.interrupted

    def is_success(self) -> bool:
        return self._inner.is_success()

    def effective_content(self) -> str:
        return self._inner.effective_content()

    @property
    def is_error(self) -> bool:
        return self._inner.is_error


@dataclass
class ToolExecution(_WrapperBase):
    """Record of a single tool invocation."""

    _inner: _core.ToolExecution

    @property
    def tool_name(self) -> str:
        return self._inner.tool_name

    @property
    def input(self) -> dict:
        return self._inner.input

    @property
    def output(self) -> ToolResult:
        return ToolResult(self._inner.output)

    @property
    def duration_ms(self) -> int:
        return self._inner.duration_ms

    @property
    def timestamp(self) -> float:
        return self._inner.timestamp

    def is_success(self) -> bool:
        return self._inner.is_success()


# Conversation tree ---------------------------------------------------------

@dataclass
class ConversationStats(_WrapperBase):
    """Basic statistics describing a conversation tree."""

    _inner: _core.ConversationStats

    @property
    def total_messages(self) -> int:
        return self._inner.total_messages

    @property
    def max_depth(self) -> int:
        return self._inner.max_depth

    @property
    def num_branches(self) -> int:
        return self._inner.num_branches

    @property
    def leaf_count(self) -> int:
        return self._inner.leaf_count


@dataclass
class ConversationNode(_WrapperBase):
    """Node in the conversation tree."""

    _inner: _core.ConversationNode

    @property
    def message(self) -> 'Message':
        return Message(self._inner.message)

    @property
    def children(self) -> List['ConversationNode']:
        return [ConversationNode(c) for c in self._inner.children]

    def child_count(self) -> int:
        return self._inner.child_count()

    def is_leaf(self) -> bool:
        return self._inner.is_leaf()


@dataclass
class ConversationTree(_WrapperBase):
    """Hierarchy of messages forming a conversation."""

    _inner: _core.ConversationTree

    @property
    def root_messages(self) -> List[ConversationNode]:
        return [ConversationNode(m) for m in self._inner.root_messages]

    @property
    def orphaned_messages(self) -> List[str]:
        return list(self._inner.orphaned_messages)

    @property
    def circular_references(self) -> List[tuple[str, str]]:
        return list(self._inner.circular_references)

    @property
    def stats(self) -> ConversationStats:
        return ConversationStats(self._inner.stats)

    def count_branches(self) -> int:
        return self._inner.count_branches()

    def max_depth(self) -> int:
        return self._inner.max_depth()


# Session related classes ---------------------------------------------------

@dataclass
class Message(_WrapperBase):
    """Conversation message wrapper.

    Wraps :class:`_core.Message`. See the README for attribute details.
    """

    _inner: _core.Message

    @property
    def role(self) -> str:
        return self._inner.role

    @property
    def text(self) -> str:
        return self._inner.text

    @property
    def cost(self) -> Optional[float]:
        return self._inner.cost

    @property
    def tools(self) -> List[str]:
        return list(self._inner.tools)

    @property
    def timestamp(self) -> float:
        return self._inner.timestamp

    @property
    def uuid(self) -> str:
        return self._inner.uuid

    @property
    def parent_uuid(self) -> Optional[str]:
        return self._inner.parent_uuid

    @property
    def is_sidechain(self) -> bool:
        return self._inner.is_sidechain

    @property
    def cwd(self) -> str:
        return self._inner.cwd

    @property
    def model(self) -> Optional[str]:
        return self._inner.model

    @property
    def stop_reason(self) -> Optional[str]:
        return self._inner.stop_reason

    @property
    def total_tokens(self) -> Optional[int]:
        return self._inner.total_tokens

    @property
    def input_tokens(self) -> Optional[int]:
        return self._inner.input_tokens

    @property
    def output_tokens(self) -> Optional[int]:
        return self._inner.output_tokens

    @property
    def usage(self) -> Optional[TokenUsage]:
        u = self._inner.usage
        return TokenUsage(u) if u is not None else None

    def get_content_blocks(self) -> List[ContentBlock]:
        return [
            _wrap_content_block(b) for b in self._inner.get_content_blocks()
        ]

    def get_text_blocks(self) -> List[TextBlock]:
        return [TextBlock(b) for b in self._inner.get_text_blocks()]

    def get_tool_blocks(self) -> List[ToolUseBlock]:
        return [ToolUseBlock(b) for b in self._inner.get_tool_blocks()]

    def has_tool_use(self) -> bool:
        return self._inner.has_tool_use()


@dataclass
class Session(_WrapperBase):
    """A complete Claude Code session.

    This class wraps :class:`_core.Session` and exposes convenient
    typed accessors. Example usage is provided in the README.
    """

    _inner: _core.Session

    def __iter__(self) -> Iterable[Message]:
        for m in self._inner:
            yield Message(m)

    def __len__(self) -> int:
        return len(self._inner)

    @property
    def session_id(self) -> str:
        return self._inner.session_id

    @property
    def messages(self) -> List[Message]:
        return [Message(m) for m in self._inner.messages]

    @property
    def total_cost(self) -> float:
        return self._inner.total_cost

    @property
    def tools_used(self) -> List[str]:
        return list(self._inner.tools_used)

    @property
    def duration(self) -> Optional[float]:
        return self._inner.duration

    @property
    def tool_costs(self) -> Dict[str, float]:
        return dict(self._inner.tool_costs)

    @property
    def cost_by_turn(self) -> List[float]:
        return list(self._inner.cost_by_turn)

    @property
    def conversation_tree(self) -> ConversationTree:
        return ConversationTree(self._inner.conversation_tree)

    @property
    def metadata(self) -> 'SessionMetadata':
        return SessionMetadata(self._inner.metadata)

    @property
    def tool_executions(self) -> List[ToolExecution]:
        return [ToolExecution(e) for e in self._inner.tool_executions]

    @property
    def project_name(self) -> str:
        return self._inner.project_name

    @property
    def project_path(self) -> Path:
        return Path(self._inner.project_path)

    def get_main_chain(self) -> List[Message]:
        return [Message(m) for m in self._inner.get_main_chain()]

    def get_messages_by_role(self, role: str) -> List[Message]:
        return [Message(m) for m in self._inner.get_messages_by_role(role)]

    def get_messages_by_tool(self, tool_name: str) -> List[Message]:
        return [Message(m) for m in self._inner.get_messages_by_tool(tool_name)]

    def get_message_by_uuid(self, uuid: str) -> Optional[Message]:
        m = self._inner.get_message_by_uuid(uuid)
        return Message(m) if m is not None else None

    def filter_messages(self, predicate: Callable[[Message], bool]) -> List[Message]:
        return [Message(m) for m in self._inner.filter_messages(lambda im: predicate(Message(im)))]

    def get_thread(self, message_uuid: str) -> List[Message]:
        return [Message(m) for m in self._inner.get_thread(message_uuid)]


@dataclass
class Project(_WrapperBase):
    """Collection of sessions under a project directory.

    See the README for examples of analyzing multiple sessions.
    """

    _inner: _core.Project

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def sessions(self) -> List[Session]:
        return [Session(s) for s in self._inner.sessions]

    @property
    def total_cost(self) -> float:
        return self._inner.total_cost

    @property
    def total_messages(self) -> int:
        return self._inner.total_messages

    @property
    def tool_usage_count(self) -> Dict[str, int]:
        return dict(self._inner.tool_usage_count)

    @property
    def total_duration(self) -> Optional[float]:
        return self._inner.total_duration


@dataclass
class SessionMetadata(_WrapperBase):
    """Aggregated statistics for a session."""

    _inner: _core.SessionMetadata

    @property
    def total_messages(self) -> int:
        return self._inner.total_messages

    @property
    def user_messages(self) -> int:
        return self._inner.user_messages

    @property
    def assistant_messages(self) -> int:
        return self._inner.assistant_messages

    @property
    def total_cost_usd(self) -> float:
        return self._inner.total_cost_usd

    @property
    def total_input_tokens(self) -> int:
        return self._inner.total_input_tokens

    @property
    def total_output_tokens(self) -> int:
        return self._inner.total_output_tokens

    @property
    def cache_creation_tokens(self) -> int:
        return self._inner.cache_creation_tokens

    @property
    def cache_read_tokens(self) -> int:
        return self._inner.cache_read_tokens

    @property
    def unique_tools_used(self) -> List[str]:
        return list(self._inner.unique_tools_used)

    @property
    def total_tool_calls(self) -> int:
        return self._inner.total_tool_calls

    @property
    def tool_usage_count(self) -> Dict[str, int]:
        return dict(self._inner.tool_usage_count)

    @property
    def session_file_path(self) -> Path:
        return Path(self._inner.session_file_path)

    @property
    def first_message_timestamp(self) -> float:
        return self._inner.first_message_timestamp

    @property
    def last_message_timestamp(self) -> float:
        return self._inner.last_message_timestamp

    @property
    def session_duration(self) -> Optional[float]:
        return self._inner.session_duration

    @property
    def total_duration_ms(self) -> Optional[int]:
        return self._inner.total_duration_ms

    @property
    def average_response_time_ms(self) -> Optional[int]:
        return self._inner.average_response_time_ms


# Helper to wrap different content block variants --------------------------

def _wrap_content_block(block: _core.TextBlock | _core.ToolUseBlock | _core.ThinkingBlock | _core.ImageBlock | _core.ToolResultBlock) -> ContentBlock:
    if isinstance(block, _core.TextBlock):
        return TextBlock(block)
    if isinstance(block, _core.ToolUseBlock):
        return ToolUseBlock(block)
    if isinstance(block, _core.ThinkingBlock):
        return ThinkingBlock(block)
    if isinstance(block, _core.ImageBlock):
        return ImageBlock(block)
    if isinstance(block, _core.ToolResultBlock):
        return ToolResultBlock(block)
    raise TypeError(f"Unexpected block type: {type(block)!r}")

