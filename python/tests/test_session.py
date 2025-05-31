"""Test Session class functionality for Rust bindings."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_sdk import Session, load, ParseError


class TestSessionLoading:
    """Test Session loading from JSONL files."""

    def test_load_valid_session(self):
        """Test loading a valid session from JSONL file."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            # Write valid session data
            f.write(json.dumps({
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello"}]
                }
            }) + "\n")
            
            f.write(json.dumps({
                "uuid": "550e8400-e29b-41d4-a716-446655440001",
                "parentUuid": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-01T12:00:01Z",
                "type": "assistant",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Hi there!"}]
                },
                "costUSD": 0.01,
                "durationMs": 1000
            }) + "\n")
            
            temp_path = Path(f.name)
        
        try:
            # Load the session
            session = load(str(temp_path))
            
            # Verify session properties
            assert isinstance(session, Session)
            assert session.session_id == "test-session"
            assert len(session) == 2
            assert session.total_messages == 2
            
        finally:
            temp_path.unlink()

    def test_load_empty_session(self):
        """Test loading an empty JSONL file."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Should raise error for empty file
            with pytest.raises(ParseError, match="Empty JSONL file"):
                load(str(temp_path))
        finally:
            temp_path.unlink()

    def test_load_malformed_json(self):
        """Test loading a file with malformed JSON."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write("{invalid json}\n")
            temp_path = Path(f.name)
        
        try:
            # Should raise error for malformed JSON
            with pytest.raises(ParseError, match="JSON"):
                load(str(temp_path))
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        with pytest.raises(ParseError, match="File not found"):
            load("/nonexistent/file.jsonl")


class TestSessionProperties:
    """Test Session properties and computed attributes."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            # Message 1: User
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Create a Python function"}]
                }
            }) + "\n")
            
            # Message 2: Assistant with tool use
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000002",
                "parentUuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:05Z",
                "type": "assistant",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll create a Python function for you."},
                        {"type": "tool_use", "id": "tool_1", "name": "str_replace_editor", "input": {
                            "command": "create",
                            "path": "example.py",
                            "file_text": "def hello():\n    print('Hello, world!')\n"
                        }}
                    ],
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                        "service_tier": "developer"
                    }
                },
                "costUSD": 0.025,
                "durationMs": 5000
            }) + "\n")
            
            # Message 3: User
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000003",
                "parentUuid": "00000000-0000-0000-0000-000000000002",
                "timestamp": "2024-01-01T12:00:10Z",
                "type": "user",
                "userType": "external",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Now run it"}]
                }
            }) + "\n")
            
            # Message 4: Assistant with another tool use
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000004",
                "parentUuid": "00000000-0000-0000-0000-000000000003",
                "timestamp": "2024-01-01T12:00:15Z",
                "type": "assistant",
                "sessionId": "test-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll run the function now."},
                        {"type": "tool_use", "id": "tool_2", "name": "bash", "input": {
                            "command": "python example.py"
                        }}
                    ]
                },
                "costUSD": 0.015,
                "durationMs": 3000
            }) + "\n")
            
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        yield session
        temp_path.unlink()

    def test_session_id(self, sample_session):
        """Test session_id property."""
        assert sample_session.session_id == "test-session"

    def test_total_messages(self, sample_session):
        """Test total_messages property."""
        assert sample_session.total_messages == 4

    def test_total_cost(self, sample_session):
        """Test total_cost property."""
        assert sample_session.total_cost == pytest.approx(0.04, rel=1e-3)

    def test_duration(self, sample_session):
        """Test duration property."""
        # Duration should be 15 seconds (from first to last message)
        assert sample_session.duration == timedelta(seconds=15)

    def test_user_messages(self, sample_session):
        """Test user_messages property."""
        assert sample_session.user_messages == 2

    def test_assistant_messages(self, sample_session):
        """Test assistant_messages property."""
        assert sample_session.assistant_messages == 2

    def test_tool_usage_summary(self, sample_session):
        """Test tool_usage_summary property."""
        tool_summary = sample_session.tool_usage_summary
        assert isinstance(tool_summary, dict)
        assert tool_summary.get("str_replace_editor") == 1
        assert tool_summary.get("bash") == 1

    def test_messages_property(self, sample_session):
        """Test messages property returns list of messages."""
        messages = sample_session.messages
        assert len(messages) == 4
        # All items should be Message objects
        for msg in messages:
            assert hasattr(msg, 'role')
            assert hasattr(msg, 'content')

    def test_start_time(self, sample_session):
        """Test start_time property."""
        start_time = sample_session.start_time
        assert isinstance(start_time, datetime)
        assert start_time.isoformat() == "2024-01-01T12:00:00+00:00"

    def test_end_time(self, sample_session):
        """Test end_time property."""
        end_time = sample_session.end_time
        assert isinstance(end_time, datetime)
        assert end_time.isoformat() == "2024-01-01T12:00:15+00:00"


class TestSessionMethods:
    """Test Session methods."""

    @pytest.fixture
    def complex_session(self):
        """Create a more complex session for testing methods."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            # Multiple messages with various content types
            messages = [
                # User message
                {
                    "uuid": f"00000000-0000-0000-0000-00000000000{i}",
                    "parentUuid": f"00000000-0000-0000-0000-00000000000{i-1}" if i > 1 else None,
                    "timestamp": f"2024-01-01T12:00:{i:02d}Z",
                    "type": "user" if i % 2 == 1 else "assistant",
                    "userType": "external",
                    "sessionId": "complex-session",
                    "version": "1.0.0",
                    "cwd": "/test",
                    "isSidechain": False,
                    "message": {
                        "role": "user" if i % 2 == 1 else "assistant",
                        "content": [{"type": "text", "text": f"Message {i}"}]
                    }
                }
                for i in range(1, 11)
            ]
            
            for msg in messages:
                f.write(json.dumps(msg) + "\n")
            
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        yield session
        temp_path.unlink()

    def test_get_messages_by_role(self, complex_session):
        """Test get_messages_by_role method."""
        # Get user messages
        user_messages = complex_session.get_messages_by_role("user")
        assert len(user_messages) == 5
        for msg in user_messages:
            assert msg.role == "user"
        
        # Get assistant messages
        assistant_messages = complex_session.get_messages_by_role("assistant")
        assert len(assistant_messages) == 5
        for msg in assistant_messages:
            assert msg.role == "assistant"

    def test_filter_messages(self, complex_session):
        """Test filter_messages method."""
        # Filter messages containing "5"
        filtered = complex_session.filter_messages(lambda msg: "5" in msg.get_text())
        assert len(filtered) == 1
        assert "Message 5" in filtered[0].get_text()
        
        # Filter all user messages
        user_msgs = complex_session.filter_messages(lambda msg: msg.role == "user")
        assert len(user_msgs) == 5

    def test_get_conversation_history(self, complex_session):
        """Test get_conversation_history method."""
        history = complex_session.get_conversation_history()
        assert isinstance(history, str)
        assert "User: Message 1" in history
        assert "Assistant: Message 2" in history
        assert history.count("User:") == 5
        assert history.count("Assistant:") == 5

    def test_iteration(self, complex_session):
        """Test iterating over session messages."""
        messages = list(complex_session)
        assert len(messages) == 10
        
        # Test that messages are in order
        for i, msg in enumerate(messages):
            assert f"Message {i+1}" in msg.get_text()

    def test_length(self, complex_session):
        """Test len() on session."""
        assert len(complex_session) == 10

    def test_getitem(self, complex_session):
        """Test indexing into session."""
        # Get first message
        first_msg = complex_session[0]
        assert "Message 1" in first_msg.get_text()
        
        # Get last message
        last_msg = complex_session[-1]
        assert "Message 10" in last_msg.get_text()
        
        # Test slicing
        slice_msgs = complex_session[2:5]
        assert len(slice_msgs) == 3
        assert "Message 3" in slice_msgs[0].get_text()


class TestSessionWithToolUse:
    """Test Session with tool use messages."""

    @pytest.fixture
    def tool_session(self):
        """Create a session with tool use."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            # User asks to create file
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "tool-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Create a file"}]
                }
            }) + "\n")
            
            # Assistant uses tool
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000002",
                "parentUuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:01Z",
                "type": "assistant",
                "sessionId": "tool-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll create a file for you."},
                        {"type": "tool_use", "id": "tool_1", "name": "str_replace_editor", "input": {
                            "command": "create",
                            "path": "test.txt",
                            "file_text": "Hello, world!"
                        }}
                    ]
                }
            }) + "\n")
            
            # Tool result (system message)
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000003",
                "parentUuid": "00000000-0000-0000-0000-000000000002",
                "timestamp": "2024-01-01T12:00:02Z",
                "type": "user",
                "userType": "internal",
                "sessionId": "tool-session",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "isMeta": True,
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": "tool_1", "content": "File created successfully", "is_error": False}]
                }
            }) + "\n")
            
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        yield session
        temp_path.unlink()

    def test_tool_usage_in_session(self, tool_session):
        """Test that tool usage is correctly tracked."""
        # Check tool usage summary
        tool_summary = tool_session.tool_usage_summary
        assert tool_summary.get("str_replace_editor") == 1
        
        # Check that we have 3 messages
        assert len(tool_session) == 3
        
        # Get the assistant message with tool use
        assistant_messages = tool_session.get_messages_by_role("assistant")
        assert len(assistant_messages) == 1
        
        # Check that the assistant message has tool use
        assistant_msg = assistant_messages[0]
        assert assistant_msg.has_tool_use()
        
        # Get tool blocks
        tool_blocks = assistant_msg.get_tool_blocks()
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["name"] == "str_replace_editor"


class TestSessionErrorHandling:
    """Test error handling in Session operations."""

    def test_invalid_role_filter(self):
        """Test get_messages_by_role with invalid role."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Test"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            # Should return empty list for invalid role
            messages = session.get_messages_by_role("invalid_role")
            assert messages == []
        finally:
            temp_path.unlink()

    def test_empty_session_properties(self):
        """Test properties on a session with minimal data."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            # Single message with no cost or duration
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "minimal",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Test"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            
            # Properties should have sensible defaults
            assert session.total_cost == 0.0
            assert session.duration == timedelta(0)
            assert session.tool_usage_summary == {}
            assert session.total_messages == 1
            
        finally:
            temp_path.unlink()