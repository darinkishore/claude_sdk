"""Test Message class functionality for Rust bindings."""

import json
import tempfile
from pathlib import Path

import pytest

from claude_sdk import load, Message


class TestMessageProperties:
    """Test Message properties and attributes."""

    @pytest.fixture
    def simple_message(self):
        """Create a simple text message."""
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
                    "content": [{"type": "text", "text": "Hello, Claude!"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        message = session.messages[0]
        yield message
        temp_path.unlink()

    @pytest.fixture
    def complex_message(self):
        """Create a complex message with multiple content types."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll help you create a Python script."},
                        {"type": "thinking", "thinking": "The user wants a Python script. I should create a simple example.", "signature": "v1"},
                        {"type": "tool_use", "id": "tool_1", "name": "str_replace_editor", "input": {
                            "command": "create",
                            "path": "script.py",
                            "file_text": "print('Hello, world!')"
                        }},
                        {"type": "text", "text": "I've created a simple Python script for you."}
                    ],
                    "usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cache_creation_input_tokens": 10,
                        "cache_read_input_tokens": 5,
                        "service_tier": "developer"
                    },
                    "model": "claude-3-opus-20240229",
                    "stop_reason": "end_turn"
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        message = session.messages[0]
        yield message
        temp_path.unlink()

    def test_message_role(self, simple_message):
        """Test message role property."""
        assert simple_message.role == "user"

    def test_message_content(self, simple_message):
        """Test message content property."""
        content = simple_message.content
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Hello, Claude!"

    def test_message_model(self, complex_message):
        """Test message model property."""
        assert complex_message.model == "claude-3-opus-20240229"

    def test_message_stop_reason(self, complex_message):
        """Test message stop_reason property."""
        assert complex_message.stop_reason == "end_turn"

    def test_message_usage(self, complex_message):
        """Test message usage property."""
        usage = complex_message.usage
        assert usage is not None
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["cache_creation_input_tokens"] == 10
        assert usage["cache_read_input_tokens"] == 5
        assert usage["service_tier"] == "developer"

    def test_message_without_usage(self, simple_message):
        """Test message without usage information."""
        assert simple_message.usage is None

    def test_message_without_model(self, simple_message):
        """Test message without model information."""
        assert simple_message.model is None

    def test_message_without_stop_reason(self, simple_message):
        """Test message without stop_reason."""
        assert simple_message.stop_reason is None


class TestMessageMethods:
    """Test Message methods."""

    @pytest.fixture
    def multi_content_message(self):
        """Create a message with multiple content blocks."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Let me help you with that."},
                        {"type": "tool_use", "id": "tool_1", "name": "bash", "input": {"command": "ls -la"}},
                        {"type": "text", "text": "Here are the files:"},
                        {"type": "tool_use", "id": "tool_2", "name": "str_replace_editor", "input": {
                            "command": "view",
                            "path": "example.py"
                        }},
                        {"type": "thinking", "thinking": "I should explain what I found.", "signature": "v1"}
                    ]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        message = session.messages[0]
        yield message
        temp_path.unlink()

    def test_get_text(self, multi_content_message):
        """Test get_text method."""
        text = multi_content_message.get_text()
        assert "Let me help you with that." in text
        assert "Here are the files:" in text
        # Should not include thinking blocks
        assert "I should explain what I found." not in text

    def test_get_text_blocks(self, multi_content_message):
        """Test get_text_blocks method."""
        text_blocks = multi_content_message.get_text_blocks()
        assert len(text_blocks) == 2
        assert text_blocks[0]["text"] == "Let me help you with that."
        assert text_blocks[1]["text"] == "Here are the files:"

    def test_get_tool_blocks(self, multi_content_message):
        """Test get_tool_blocks method."""
        tool_blocks = multi_content_message.get_tool_blocks()
        assert len(tool_blocks) == 2
        assert tool_blocks[0]["name"] == "bash"
        assert tool_blocks[0]["input"]["command"] == "ls -la"
        assert tool_blocks[1]["name"] == "str_replace_editor"

    def test_has_tool_use(self, multi_content_message):
        """Test has_tool_use method."""
        assert multi_content_message.has_tool_use() is True

    def test_has_tool_use_false(self):
        """Test has_tool_use returns False for messages without tools."""
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
                    "content": [{"type": "text", "text": "Just text"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            message = session.messages[0]
            assert message.has_tool_use() is False
        finally:
            temp_path.unlink()

    def test_empty_content_methods(self):
        """Test methods on a message with empty content."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": []
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            message = session.messages[0]
            
            assert message.get_text() == ""
            assert message.get_text_blocks() == []
            assert message.get_tool_blocks() == []
            assert message.has_tool_use() is False
        finally:
            temp_path.unlink()


class TestMessageTokenInformation:
    """Test Message token information access."""

    @pytest.fixture
    def message_with_tokens(self):
        """Create a message with token usage information."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Here's my response."}],
                    "usage": {
                        "input_tokens": 150,
                        "output_tokens": 75,
                        "cache_creation_input_tokens": 20,
                        "cache_read_input_tokens": 30,
                        "service_tier": "developer"
                    }
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        message = session.messages[0]
        yield message
        temp_path.unlink()

    def test_input_tokens(self, message_with_tokens):
        """Test input_tokens property."""
        assert message_with_tokens.input_tokens == 150

    def test_output_tokens(self, message_with_tokens):
        """Test output_tokens property."""
        assert message_with_tokens.output_tokens == 75

    def test_total_tokens(self, message_with_tokens):
        """Test total_tokens property."""
        assert message_with_tokens.total_tokens == 225  # 150 + 75

    def test_cache_creation_tokens(self, message_with_tokens):
        """Test cache_creation_input_tokens property."""
        assert message_with_tokens.cache_creation_input_tokens == 20

    def test_cache_read_tokens(self, message_with_tokens):
        """Test cache_read_input_tokens property."""
        assert message_with_tokens.cache_read_input_tokens == 30

    def test_tokens_without_usage(self):
        """Test token properties on message without usage data."""
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
                    "content": [{"type": "text", "text": "Hello"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            message = session.messages[0]
            
            # Should return 0 for all token counts
            assert message.input_tokens == 0
            assert message.output_tokens == 0
            assert message.total_tokens == 0
            assert message.cache_creation_input_tokens == 0
            assert message.cache_read_input_tokens == 0
        finally:
            temp_path.unlink()


class TestMessageWithThinkingBlocks:
    """Test Message handling of thinking blocks."""

    @pytest.fixture
    def thinking_message(self):
        """Create a message with thinking blocks."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "Let me think about this request.", "signature": "v1"},
                        {"type": "text", "text": "I understand your request."},
                        {"type": "thinking", "thinking": "I should provide a detailed response.", "signature": "v1"},
                        {"type": "text", "text": "Here's my detailed answer."}
                    ]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        session = load(str(temp_path))
        message = session.messages[0]
        yield message
        temp_path.unlink()

    def test_thinking_blocks_excluded_from_text(self, thinking_message):
        """Test that thinking blocks are excluded from get_text()."""
        text = thinking_message.get_text()
        assert "I understand your request." in text
        assert "Here's my detailed answer." in text
        # Thinking content should not be included
        assert "Let me think about this request." not in text
        assert "I should provide a detailed response." not in text

    def test_get_thinking_blocks(self, thinking_message):
        """Test getting thinking blocks if supported."""
        # This might not be implemented in the Rust bindings yet
        # but we can test the content structure
        content = thinking_message.content
        thinking_blocks = [c for c in content if c.get("type") == "thinking"]
        assert len(thinking_blocks) == 2
        assert thinking_blocks[0]["thinking"] == "Let me think about this request."
        assert thinking_blocks[1]["thinking"] == "I should provide a detailed response."


class TestMessageEdgeCases:
    """Test edge cases and error handling for Message."""

    def test_message_with_unknown_content_type(self):
        """Test message with unknown content type."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T12:00:00Z",
                "type": "assistant",
                "sessionId": "test",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Normal text"},
                        {"type": "unknown_type", "data": "some data"},
                        {"type": "text", "text": "More text"}
                    ]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            message = session.messages[0]
            
            # Should handle unknown types gracefully
            text = message.get_text()
            assert "Normal text" in text
            assert "More text" in text
            
            text_blocks = message.get_text_blocks()
            assert len(text_blocks) == 2
        finally:
            temp_path.unlink()

    def test_message_repr(self):
        """Test string representation of Message."""
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
                    "content": [{"type": "text", "text": "Test message"}]
                }
            }) + "\n")
            temp_path = Path(f.name)
        
        try:
            session = load(str(temp_path))
            message = session.messages[0]
            
            # Should have a reasonable string representation
            repr_str = repr(message)
            assert "Message" in repr_str
            assert "user" in repr_str.lower()
        finally:
            temp_path.unlink()