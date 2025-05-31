"""End-to-end integration tests for Rust bindings."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_sdk import (
    Session, Message, Project,
    load, load_project, find_sessions, find_projects,
    ParseError, ValidationError, SessionError
)


class TestCompleteWorkflow:
    """Test complete workflows using the SDK."""

    def test_analyze_coding_session(self):
        """Test analyzing a realistic coding session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "coding_session.jsonl"
            
            # Create a realistic coding session
            with open(session_file, "w") as f:
                # User asks to create a Python script
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "coding-session",
                    "version": "1.0.0",
                    "cwd": str(tmpdir),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Create a Python script to analyze CSV files"}]
                    }
                }) + "\n")
                
                # Assistant creates the script
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000002",
                    "parentUuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T10:00:05Z",
                    "type": "assistant",
                    "sessionId": "coding-session",
                    "version": "1.0.0",
                    "cwd": str(tmpdir),
                    "isSidechain": False,
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I'll create a Python script to analyze CSV files with pandas."},
                            {"type": "tool_use", "id": "tool_1", "name": "str_replace_editor", "input": {
                                "command": "create",
                                "path": "csv_analyzer.py",
                                "file_text": """import pandas as pd
import sys

def analyze_csv(filename):
    df = pd.read_csv(filename)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\\nSummary:\\n{df.describe()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python csv_analyzer.py <file.csv>")
        sys.exit(1)
    analyze_csv(sys.argv[1])
"""
                            }}
                        ],
                        "usage": {
                            "input_tokens": 150,
                            "output_tokens": 200,
                            "cache_creation_input_tokens": 0,
                            "cache_read_input_tokens": 0,
                            "service_tier": "developer"
                        }
                    },
                    "costUSD": 0.025,
                    "durationMs": 5000
                }) + "\n")
                
                # User asks to test it
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000003",
                    "parentUuid": "00000000-0000-0000-0000-000000000002",
                    "timestamp": "2024-01-01T10:00:10Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "coding-session",
                    "version": "1.0.0",
                    "cwd": str(tmpdir),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Now create a sample CSV and test the script"}]
                    }
                }) + "\n")
                
                # Assistant creates CSV and runs script
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000004",
                    "parentUuid": "00000000-0000-0000-0000-000000000003",
                    "timestamp": "2024-01-01T10:00:15Z",
                    "type": "assistant",
                    "sessionId": "coding-session",
                    "version": "1.0.0",
                    "cwd": str(tmpdir),
                    "isSidechain": False,
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I'll create a sample CSV file and test the script."},
                            {"type": "tool_use", "id": "tool_2", "name": "str_replace_editor", "input": {
                                "command": "create",
                                "path": "sample_data.csv",
                                "file_text": "name,age,score\nAlice,25,85\nBob,30,92\nCharlie,35,78\nDiana,28,95\n"
                            }},
                            {"type": "tool_use", "id": "tool_3", "name": "bash", "input": {
                                "command": "python csv_analyzer.py sample_data.csv"
                            }}
                        ]
                    },
                    "costUSD": 0.015,
                    "durationMs": 3000
                }) + "\n")
            
            # Load and analyze the session
            session = load(str(session_file))
            
            # Verify session properties
            assert session.session_id == "coding-session"
            assert session.total_messages == 4
            assert session.total_cost == pytest.approx(0.04, rel=1e-3)
            assert session.duration == timedelta(seconds=15)
            
            # Check tool usage
            tool_summary = session.tool_usage_summary
            assert tool_summary["str_replace_editor"] == 2
            assert tool_summary["bash"] == 1
            
            # Analyze messages
            user_messages = session.get_messages_by_role("user")
            assert len(user_messages) == 2
            
            assistant_messages = session.get_messages_by_role("assistant")
            assert len(assistant_messages) == 2
            
            # Check that all assistant messages used tools
            for msg in assistant_messages:
                assert msg.has_tool_use()
            
            # Get conversation history
            history = session.get_conversation_history()
            assert "Create a Python script" in history
            assert "pandas" in history
            assert "sample CSV" in history

    def test_multi_session_project_analysis(self):
        """Test analyzing a project with multiple related sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "web_app_project"
            project_dir.mkdir()
            
            # Session 1: Initial setup
            session1_file = project_dir / "01_setup.jsonl"
            with open(session1_file, "w") as f:
                messages = [
                    ("user", "Set up a new Flask web application", None),
                    ("assistant", "I'll help you set up a Flask application.", 0.02),
                    ("user", "Add user authentication", None),
                    ("assistant", "I'll add authentication using Flask-Login.", 0.03),
                ]
                
                for i, (role, text, cost) in enumerate(messages):
                    msg_data = {
                        "uuid": f"01{i:06d}-0000-0000-0000-000000000001",
                        "parentUuid": f"01{i-1:06d}-0000-0000-0000-000000000001" if i > 0 else None,
                        "timestamp": f"2024-01-01T09:{i*5:02d}:00Z",
                        "type": role,
                        "sessionId": "setup-session",
                        "version": "1.0.0",
                        "cwd": str(project_dir),
                        "isSidechain": False,
                        "message": {
                            "role": role,
                            "content": [{"type": "text", "text": text}]
                        }
                    }
                    
                    if role == "user":
                        msg_data["userType"] = "external"
                    else:
                        msg_data["costUSD"] = cost
                        msg_data["message"]["content"].append({
                            "type": "tool_use",
                            "id": f"tool_{i}",
                            "name": "str_replace_editor",
                            "input": {"command": "create", "path": f"file_{i}.py"}
                        })
                    
                    f.write(json.dumps(msg_data) + "\n")
            
            # Session 2: Feature development
            session2_file = project_dir / "02_features.jsonl"
            with open(session2_file, "w") as f:
                messages = [
                    ("user", "Add a REST API for user management", None),
                    ("assistant", "I'll create REST API endpoints.", 0.04),
                    ("user", "Add database models", None),
                    ("assistant", "I'll set up SQLAlchemy models.", 0.03),
                    ("user", "Add unit tests", None),
                    ("assistant", "I'll create comprehensive unit tests.", 0.05),
                ]
                
                for i, (role, text, cost) in enumerate(messages):
                    msg_data = {
                        "uuid": f"02{i:06d}-0000-0000-0000-000000000001",
                        "parentUuid": f"02{i-1:06d}-0000-0000-0000-000000000001" if i > 0 else None,
                        "timestamp": f"2024-01-02T10:{i*10:02d}:00Z",
                        "type": role,
                        "sessionId": "features-session",
                        "version": "1.0.0",
                        "cwd": str(project_dir),
                        "isSidechain": False,
                        "message": {
                            "role": role,
                            "content": [{"type": "text", "text": text}]
                        }
                    }
                    
                    if role == "user":
                        msg_data["userType"] = "external"
                    else:
                        msg_data["costUSD"] = cost
                        # Mix of tools
                        if "test" in text.lower():
                            tool_name = "bash"
                            tool_input = {"command": "pytest"}
                        else:
                            tool_name = "str_replace_editor"
                            tool_input = {"command": "edit", "path": "app.py"}
                        
                        msg_data["message"]["content"].append({
                            "type": "tool_use",
                            "id": f"tool_{i}",
                            "name": tool_name,
                            "input": tool_input
                        })
                    
                    f.write(json.dumps(msg_data) + "\n")
            
            # Session 3: Debugging
            session3_file = project_dir / "03_debugging.jsonl"
            with open(session3_file, "w") as f:
                messages = [
                    ("user", "There's a bug in the authentication", None),
                    ("assistant", "Let me investigate the issue.", 0.02),
                    ("user", "The session isn't persisting", None),
                    ("assistant", "I found the issue and will fix it.", 0.03),
                ]
                
                for i, (role, text, cost) in enumerate(messages):
                    msg_data = {
                        "uuid": f"03{i:06d}-0000-0000-0000-000000000001",
                        "parentUuid": f"03{i-1:06d}-0000-0000-0000-000000000001" if i > 0 else None,
                        "timestamp": f"2024-01-03T14:{i*15:02d}:00Z",
                        "type": role,
                        "sessionId": "debug-session",
                        "version": "1.0.0",
                        "cwd": str(project_dir),
                        "isSidechain": False,
                        "message": {
                            "role": role,
                            "content": [{"type": "text", "text": text}]
                        }
                    }
                    
                    if role == "user":
                        msg_data["userType"] = "external"
                    else:
                        msg_data["costUSD"] = cost
                        msg_data["message"]["content"].append({
                            "type": "tool_use",
                            "id": f"tool_{i}",
                            "name": "read",
                            "input": {"path": "auth.py"}
                        })
                    
                    f.write(json.dumps(msg_data) + "\n")
            
            # Load the project
            project = load_project(str(project_dir))
            
            # Verify project properties
            assert project.name == "web_app_project"
            assert project.total_sessions == 3
            assert project.total_messages == 14  # 4 + 6 + 4
            assert project.total_cost == pytest.approx(0.22, rel=1e-3)  # Sum of all costs
            
            # Check sessions are in chronological order
            sessions = project.sessions
            assert sessions[0].session_id == "setup-session"
            assert sessions[1].session_id == "features-session"
            assert sessions[2].session_id == "debug-session"
            
            # Analyze tool usage across project
            tool_summary = project.get_tool_usage_summary()
            assert tool_summary["str_replace_editor"] == 4  # 2 + 2 + 0
            assert tool_summary["bash"] == 1
            assert tool_summary["read"] == 2
            
            # Find expensive sessions
            expensive = project.get_most_expensive_sessions(n=2)
            assert len(expensive) == 2
            assert expensive[0].session_id == "features-session"  # 0.12
            assert expensive[1].session_id == "setup-session"    # 0.05
            
            # Filter by date
            jan2_sessions = project.get_sessions_by_date_range(
                datetime(2024, 1, 2),
                datetime(2024, 1, 3)
            )
            assert len(jan2_sessions) == 1
            assert jan2_sessions[0].session_id == "features-session"
            
            # Filter by criteria
            test_sessions = project.filter_sessions(
                lambda s: any("test" in msg.get_text().lower() for msg in s.messages)
            )
            assert len(test_sessions) == 1
            assert test_sessions[0].session_id == "features-session"


class TestRealWorldScenarios:
    """Test scenarios based on real-world usage patterns."""

    def test_interrupted_session_handling(self):
        """Test handling sessions that were interrupted or incomplete."""
        with tempfile.TemporaryFile(suffix=".jsonl", mode="w+") as f:
            # Session starts normally
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "interrupted",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Help me refactor this code"}]
                }
            }) + "\n")
            
            # Assistant starts responding
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000002",
                "parentUuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:05Z",
                "type": "assistant",
                "sessionId": "interrupted",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "I'll help you refactor the code. Let me analyze it first."},
                        {"type": "tool_use", "id": "tool_1", "name": "read", "input": {"path": "main.py"}}
                    ]
                }
                # Note: No costUSD or durationMs - session was interrupted
            }) + "\n")
            
            # Tool result comes in
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000003",
                "parentUuid": "00000000-0000-0000-0000-000000000002",
                "timestamp": "2024-01-01T10:00:06Z",
                "type": "user",
                "userType": "internal",
                "sessionId": "interrupted",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "isMeta": True,
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": "tool_1", "content": "File content here", "is_error": False}]
                }
            }) + "\n")
            
            # Session ends abruptly - no further assistant response
            
            f.seek(0)
            session = load(f.name)
            
            # Should handle incomplete session gracefully
            assert session.total_messages == 3
            assert session.total_cost == 0.0  # No cost recorded
            assert session.tool_usage_summary["read"] == 1
            
            # Last message should be the tool result
            assert session.messages[-1].content[0]["type"] == "tool_result"

    def test_branching_conversation(self):
        """Test handling branching conversations with sidechains."""
        with tempfile.TemporaryFile(suffix=".jsonl", mode="w+") as f:
            # Main conversation thread
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "branching",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Write a sorting algorithm"}]
                }
            }) + "\n")
            
            # First approach
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000002",
                "parentUuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:05Z",
                "type": "assistant",
                "sessionId": "branching",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "I'll implement a bubble sort algorithm."}]
                }
            }) + "\n")
            
            # User decides to try different approach (sidechain)
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000003",
                "parentUuid": "00000000-0000-0000-0000-000000000001",  # Branches from original request
                "timestamp": "2024-01-01T10:00:10Z",
                "type": "assistant",
                "sessionId": "branching",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": True,  # This is a sidechain
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "I'll implement a quicksort algorithm instead."}]
                }
            }) + "\n")
            
            # Continue with sidechain
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000004",
                "parentUuid": "00000000-0000-0000-0000-000000000003",
                "timestamp": "2024-01-01T10:00:15Z",
                "type": "user",
                "userType": "external",
                "sessionId": "branching",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": True,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Yes, use quicksort"}]
                }
            }) + "\n")
            
            f.seek(0)
            session = load(f.name)
            
            # Should include all messages including sidechains
            assert session.total_messages == 4
            
            # Can analyze branching structure if needed
            main_chain = [msg for msg in session.messages if not hasattr(msg, 'is_sidechain') or not msg.is_sidechain]
            sidechains = [msg for msg in session.messages if hasattr(msg, 'is_sidechain') and msg.is_sidechain]
            
            # This depends on how the Rust implementation handles sidechains
            # Adjust assertions based on actual behavior


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_mixed_session_ids_in_file(self):
        """Test handling file with mixed session IDs."""
        with tempfile.TemporaryFile(suffix=".jsonl", mode="w+") as f:
            # Message from session A
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "session-a",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Message A"}]
                }
            }) + "\n")
            
            # Message from session B (different session!)
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000002",
                "timestamp": "2024-01-01T10:00:05Z",
                "type": "user",
                "userType": "external",
                "sessionId": "session-b",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Message B"}]
                }
            }) + "\n")
            
            f.seek(0)
            
            # Should either handle gracefully or raise an error
            # Behavior depends on implementation
            try:
                session = load(f.name)
                # If it loads, should probably use first session ID
                assert session.session_id in ["session-a", "session-b"]
            except (ParseError, ValidationError):
                # This is also acceptable behavior
                pass

    def test_future_timestamp_handling(self):
        """Test handling messages with future timestamps."""
        with tempfile.TemporaryFile(suffix=".jsonl", mode="w+") as f:
            # Message with future timestamp
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2099-01-01T10:00:00Z",  # Far future
                "type": "user",
                "userType": "external",
                "sessionId": "future",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Future message"}]
                }
            }) + "\n")
            
            f.seek(0)
            session = load(f.name)
            
            # Should handle future timestamps
            assert session.total_messages == 1
            assert session.start_time.year == 2099

    def test_very_large_message_content(self):
        """Test handling very large message content."""
        with tempfile.TemporaryFile(suffix=".jsonl", mode="w+") as f:
            # Create a very large text content
            large_text = "x" * 1_000_000  # 1MB of text
            
            f.write(json.dumps({
                "uuid": "00000000-0000-0000-0000-000000000001",
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "user",
                "userType": "external",
                "sessionId": "large",
                "version": "1.0.0",
                "cwd": "/test",
                "isSidechain": False,
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": large_text}]
                }
            }) + "\n")
            
            f.seek(0)
            session = load(f.name)
            
            # Should handle large content
            assert session.total_messages == 1
            assert len(session.messages[0].get_text()) == 1_000_000


class TestPerformanceWithLargeDatasets:
    """Test performance with large datasets."""

    def test_project_with_many_sessions(self):
        """Test loading project with many sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "large_project"
            project_dir.mkdir()
            
            # Create 50 session files
            for i in range(50):
                session_file = project_dir / f"session_{i:03d}.jsonl"
                with open(session_file, "w") as f:
                    # Each session has 10 messages
                    for j in range(10):
                        role = "user" if j % 2 == 0 else "assistant"
                        msg_type = "user" if j % 2 == 0 else "assistant"
                        
                        msg_data = {
                            "uuid": f"{i:03d}{j:03d}-0000-0000-0000-000000000001",
                            "parentUuid": f"{i:03d}{j-1:03d}-0000-0000-0000-000000000001" if j > 0 else None,
                            "timestamp": f"2024-01-01T{10+i//10:02d}:{(i%10)*6:02d}:{j:02d}Z",
                            "type": msg_type,
                            "sessionId": f"session-{i:03d}",
                            "version": "1.0.0",
                            "cwd": str(project_dir),
                            "isSidechain": False,
                            "message": {
                                "role": role,
                                "content": [{"type": "text", "text": f"Message {j} in session {i}"}]
                            }
                        }
                        
                        if role == "user":
                            msg_data["userType"] = "external"
                        else:
                            msg_data["costUSD"] = 0.001
                        
                        f.write(json.dumps(msg_data) + "\n")
            
            import time
            start_time = time.time()
            
            # Load the large project
            project = load_project(str(project_dir))
            
            load_time = time.time() - start_time
            
            # Verify it loaded correctly
            assert project.total_sessions == 50
            assert project.total_messages == 500  # 50 sessions * 10 messages
            
            # Performance check - should load reasonably fast
            assert load_time < 5.0  # Should load in under 5 seconds
            
            # Test operations on large project
            start_time = time.time()
            
            # Filter operations
            expensive = project.get_most_expensive_sessions(n=10)
            filtered = project.filter_sessions(lambda s: s.total_messages > 5)
            tool_summary = project.get_tool_usage_summary()
            
            operation_time = time.time() - start_time
            
            # Operations should be fast
            assert operation_time < 1.0  # Should complete in under 1 second