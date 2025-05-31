"""Pytest configuration and fixtures for claude_sdk tests."""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w+", delete=False) as f:
        # Write a minimal valid session
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
                "content": [{"type": "text", "text": "Test message"}]
            }
        }) + "\n")
        
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
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
            "content": [{"type": "text", "text": "Hello, Claude!"}]
        }
    }


@pytest.fixture
def sample_assistant_message_data():
    """Sample assistant message data with usage info."""
    return {
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "parentUuid": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-01T12:00:05Z",
        "type": "assistant",
        "sessionId": "test-session",
        "version": "1.0.0",
        "cwd": "/test",
        "isSidechain": False,
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello! I'm Claude, an AI assistant."},
                {"type": "tool_use", "id": "tool_1", "name": "get_weather", "input": {"location": "San Francisco"}}
            ],
            "model": "claude-3-opus-20240229",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 10,
                "service_tier": "developer"
            }
        },
        "costUSD": 0.025,
        "durationMs": 1500
    }


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()
        
        # Create a few sample sessions
        for i in range(3):
            session_file = project_path / f"session_{i}.jsonl"
            with open(session_file, "w") as f:
                # Write minimal session data
                f.write(json.dumps({
                    "uuid": f"{i:08d}-0000-0000-0000-000000000001",
                    "timestamp": f"2024-01-0{i+1}T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": f"session-{i}",
                    "version": "1.0.0",
                    "cwd": str(project_path),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": f"Session {i} start"}]
                    }
                }) + "\n")
        
        yield project_path