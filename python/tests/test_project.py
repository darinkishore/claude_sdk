"""Test Project class functionality for Rust bindings."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_sdk import Project, load_project, ParseError


class TestProjectLoading:
    """Test Project loading functionality."""

    @pytest.fixture
    def project_dir(self):
        """Create a temporary project directory with sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            # Create multiple session files
            for i in range(3):
                session_file = project_path / f"session_{i}.jsonl"
                with open(session_file, "w") as f:
                    # Write a simple session
                    f.write(json.dumps({
                        "uuid": f"00000000-0000-0000-0000-00000000{i}001",
                        "timestamp": f"2024-01-0{i+1}T12:00:00Z",
                        "type": "user",
                        "userType": "external",
                        "sessionId": f"session-{i}",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": f"Session {i} message"}]
                        }
                    }) + "\n")
                    
                    # Add assistant response with cost
                    f.write(json.dumps({
                        "uuid": f"00000000-0000-0000-0000-00000000{i}002",
                        "parentUuid": f"00000000-0000-0000-0000-00000000{i}001",
                        "timestamp": f"2024-01-0{i+1}T12:00:05Z",
                        "type": "assistant",
                        "sessionId": f"session-{i}",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": f"Response for session {i}"}]
                        },
                        "costUSD": 0.01 * (i + 1),
                        "durationMs": 1000 * (i + 1)
                    }) + "\n")
            
            yield project_path

    def test_load_project(self, project_dir):
        """Test loading a project directory."""
        project = load_project(str(project_dir))
        
        assert isinstance(project, Project)
        assert project.path == str(project_dir)
        assert len(project.sessions) == 3

    def test_load_project_nonexistent(self):
        """Test loading a non-existent project directory."""
        with pytest.raises(ParseError, match="not found"):
            load_project("/nonexistent/project")

    def test_load_empty_project(self):
        """Test loading a project with no sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_project = Path(tmpdir) / "empty_project"
            empty_project.mkdir()
            
            project = load_project(str(empty_project))
            assert len(project.sessions) == 0


class TestProjectProperties:
    """Test Project properties and computed attributes."""

    @pytest.fixture
    def sample_project(self, project_dir):
        """Load a sample project for testing."""
        return load_project(str(project_dir))

    def test_project_path(self, sample_project):
        """Test project path property."""
        assert sample_project.path.endswith("test_project")

    def test_project_name(self, sample_project):
        """Test project name property."""
        assert sample_project.name == "test_project"

    def test_total_sessions(self, sample_project):
        """Test total_sessions property."""
        assert sample_project.total_sessions == 3

    def test_total_messages(self, sample_project):
        """Test total_messages property."""
        # Each session has 2 messages
        assert sample_project.total_messages == 6

    def test_total_cost(self, sample_project):
        """Test total_cost property."""
        # Costs: 0.01 + 0.02 + 0.03 = 0.06
        assert sample_project.total_cost == pytest.approx(0.06, rel=1e-3)

    def test_total_duration(self, sample_project):
        """Test total_duration property."""
        # Each session duration is 5 seconds
        assert sample_project.total_duration == timedelta(seconds=15)

    def test_sessions_property(self, sample_project):
        """Test sessions property returns list of Session objects."""
        sessions = sample_project.sessions
        assert len(sessions) == 3
        
        # Verify sessions are sorted by start time
        for i, session in enumerate(sessions):
            assert session.session_id == f"session-{i}"


class TestProjectMethods:
    """Test Project methods."""

    @pytest.fixture
    def complex_project(self):
        """Create a project with various session types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "complex_project"
            project_path.mkdir()
            
            # Session 1: High cost, many tools
            session1 = project_path / "expensive_session.jsonl"
            with open(session1, "w") as f:
                for i in range(5):
                    # User message
                    f.write(json.dumps({
                        "uuid": f"10000000-0000-0000-0000-00000000{i:04d}",
                        "parentUuid": f"10000000-0000-0000-0000-00000000{i-1:04d}" if i > 0 else None,
                        "timestamp": f"2024-01-01T12:{i*2:02d}:00Z",
                        "type": "user",
                        "userType": "external",
                        "sessionId": "expensive-session",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": f"Request {i}"}]
                        }
                    }) + "\n")
                    
                    # Assistant with tool use
                    f.write(json.dumps({
                        "uuid": f"10000000-0000-0000-0000-00000001{i:04d}",
                        "parentUuid": f"10000000-0000-0000-0000-00000000{i:04d}",
                        "timestamp": f"2024-01-01T12:{i*2+1:02d}:00Z",
                        "type": "assistant",
                        "sessionId": "expensive-session",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"type": "text", "text": f"Using tool for request {i}"},
                                {"type": "tool_use", "id": f"tool_{i}", "name": "bash", "input": {"command": "echo test"}}
                            ]
                        },
                        "costUSD": 0.05,
                        "durationMs": 2000
                    }) + "\n")
            
            # Session 2: Low cost, no tools
            session2 = project_path / "simple_session.jsonl"
            with open(session2, "w") as f:
                f.write(json.dumps({
                    "uuid": "20000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-02T10:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "simple-session",
                    "version": "1.0.0",
                    "cwd": str(project_path),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Simple request"}]
                    }
                }) + "\n")
                
                f.write(json.dumps({
                    "uuid": "20000000-0000-0000-0000-000000000002",
                    "parentUuid": "20000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-02T10:00:01Z",
                    "type": "assistant",
                    "sessionId": "simple-session",
                    "version": "1.0.0",
                    "cwd": str(project_path),
                    "isSidechain": False,
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Simple response"}]
                    },
                    "costUSD": 0.001,
                    "durationMs": 500
                }) + "\n")
            
            # Session 3: Medium complexity
            session3 = project_path / "medium_session.jsonl"
            with open(session3, "w") as f:
                for i in range(3):
                    f.write(json.dumps({
                        "uuid": f"30000000-0000-0000-0000-00000000{i*2+1:04d}",
                        "parentUuid": f"30000000-0000-0000-0000-00000000{i*2:04d}" if i > 0 else None,
                        "timestamp": f"2024-01-03T14:{i*5:02d}:00Z",
                        "type": "user",
                        "userType": "external",
                        "sessionId": "medium-session",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": f"Medium request {i}"}]
                        }
                    }) + "\n")
                    
                    f.write(json.dumps({
                        "uuid": f"30000000-0000-0000-0000-00000000{i*2+2:04d}",
                        "parentUuid": f"30000000-0000-0000-0000-00000000{i*2+1:04d}",
                        "timestamp": f"2024-01-03T14:{i*5+2:02d}:00Z",
                        "type": "assistant",
                        "sessionId": "medium-session",
                        "version": "1.0.0",
                        "cwd": str(project_path),
                        "isSidechain": False,
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": f"Medium response {i}"}]
                        },
                        "costUSD": 0.01,
                        "durationMs": 1500
                    }) + "\n")
            
            yield load_project(str(project_path))

    def test_filter_sessions_by_cost(self, complex_project):
        """Test filter_sessions method with cost criteria."""
        # Filter sessions with cost > $0.10
        expensive_sessions = complex_project.filter_sessions(
            lambda s: s.total_cost > 0.10
        )
        assert len(expensive_sessions) == 1
        assert expensive_sessions[0].session_id == "expensive-session"
        
        # Filter cheap sessions
        cheap_sessions = complex_project.filter_sessions(
            lambda s: s.total_cost < 0.01
        )
        assert len(cheap_sessions) == 1
        assert cheap_sessions[0].session_id == "simple-session"

    def test_filter_sessions_by_message_count(self, complex_project):
        """Test filter_sessions by message count."""
        # Sessions with more than 5 messages
        large_sessions = complex_project.filter_sessions(
            lambda s: s.total_messages > 5
        )
        assert len(large_sessions) == 1
        assert large_sessions[0].session_id == "expensive-session"

    def test_filter_sessions_by_tool_usage(self, complex_project):
        """Test filter_sessions by tool usage."""
        # Sessions that use tools
        tool_sessions = complex_project.filter_sessions(
            lambda s: len(s.tool_usage_summary) > 0
        )
        assert len(tool_sessions) == 1
        assert tool_sessions[0].session_id == "expensive-session"

    def test_get_sessions_by_date_range(self, complex_project):
        """Test get_sessions_by_date_range method."""
        # Get sessions from Jan 2
        start_date = datetime(2024, 1, 2)
        end_date = datetime(2024, 1, 3)
        
        sessions = complex_project.get_sessions_by_date_range(start_date, end_date)
        assert len(sessions) == 1
        assert sessions[0].session_id == "simple-session"
        
        # Get all sessions
        all_sessions = complex_project.get_sessions_by_date_range(
            datetime(2024, 1, 1),
            datetime(2024, 1, 4)
        )
        assert len(all_sessions) == 3

    def test_get_most_expensive_sessions(self, complex_project):
        """Test get_most_expensive_sessions method."""
        # Get top 2 most expensive
        top_sessions = complex_project.get_most_expensive_sessions(n=2)
        assert len(top_sessions) == 2
        assert top_sessions[0].session_id == "expensive-session"
        assert top_sessions[1].session_id == "medium-session"
        
        # Verify they're sorted by cost
        assert top_sessions[0].total_cost > top_sessions[1].total_cost

    def test_get_tool_usage_summary(self, complex_project):
        """Test get_tool_usage_summary method."""
        tool_summary = complex_project.get_tool_usage_summary()
        assert isinstance(tool_summary, dict)
        assert tool_summary.get("bash") == 5  # Used 5 times in expensive session

    def test_iteration(self, complex_project):
        """Test iterating over project sessions."""
        sessions = list(complex_project)
        assert len(sessions) == 3
        
        # Should be sorted by start time
        session_ids = [s.session_id for s in sessions]
        assert session_ids == ["expensive-session", "simple-session", "medium-session"]

    def test_length(self, complex_project):
        """Test len() on project."""
        assert len(complex_project) == 3

    def test_getitem(self, complex_project):
        """Test indexing into project sessions."""
        # Get first session
        assert complex_project[0].session_id == "expensive-session"
        
        # Get last session
        assert complex_project[-1].session_id == "medium-session"
        
        # Test slicing
        middle_sessions = complex_project[1:3]
        assert len(middle_sessions) == 2
        assert middle_sessions[0].session_id == "simple-session"


class TestProjectAggregation:
    """Test Project aggregation functionality."""

    @pytest.fixture
    def stats_project(self):
        """Create a project for testing statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "stats_project"
            project_path.mkdir()
            
            # Create sessions with known statistics
            for day in range(1, 4):
                session_file = project_path / f"day{day}_session.jsonl"
                with open(session_file, "w") as f:
                    # Each day has different patterns
                    for hour in range(3):
                        msg_idx = (day - 1) * 6 + hour * 2
                        
                        # User message
                        f.write(json.dumps({
                            "uuid": f"{day:02d}{hour:02d}00000-0000-0000-0000-000000000001",
                            "timestamp": f"2024-01-{day:02d}T{10+hour:02d}:00:00Z",
                            "type": "user",
                            "userType": "external",
                            "sessionId": f"day{day}-session",
                            "version": "1.0.0",
                            "cwd": str(project_path),
                            "isSidechain": False,
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": f"Day {day} hour {hour}"}]
                            }
                        }) + "\n")
                        
                        # Assistant response
                        tools = []
                        if day == 1:  # Day 1: lots of bash
                            tools = [{"type": "tool_use", "id": f"t{hour}", "name": "bash", "input": {"command": "ls"}}]
                        elif day == 2:  # Day 2: mix of tools
                            tool_name = ["str_replace_editor", "bash", "read"][hour]
                            tools = [{"type": "tool_use", "id": f"t{hour}", "name": tool_name, "input": {}}]
                        
                        f.write(json.dumps({
                            "uuid": f"{day:02d}{hour:02d}00000-0000-0000-0000-000000000002",
                            "parentUuid": f"{day:02d}{hour:02d}00000-0000-0000-0000-000000000001",
                            "timestamp": f"2024-01-{day:02d}T{10+hour:02d}:01:00Z",
                            "type": "assistant",
                            "sessionId": f"day{day}-session",
                            "version": "1.0.0",
                            "cwd": str(project_path),
                            "isSidechain": False,
                            "message": {
                                "role": "assistant",
                                "content": [{"type": "text", "text": f"Response {hour}"}] + tools
                            },
                            "costUSD": 0.01 * day,  # Increasing cost per day
                            "durationMs": 1000 * (hour + 1)
                        }) + "\n")
            
            yield load_project(str(project_path))

    def test_average_session_cost(self, stats_project):
        """Test calculating average session cost."""
        # Day 1: 3 * 0.01 = 0.03
        # Day 2: 3 * 0.02 = 0.06
        # Day 3: 3 * 0.03 = 0.09
        # Total: 0.18 / 3 sessions = 0.06
        avg_cost = stats_project.total_cost / stats_project.total_sessions
        assert avg_cost == pytest.approx(0.06, rel=1e-3)

    def test_messages_per_session(self, stats_project):
        """Test calculating messages per session."""
        # Each session has 6 messages
        avg_messages = stats_project.total_messages / stats_project.total_sessions
        assert avg_messages == 6

    def test_tool_usage_distribution(self, stats_project):
        """Test tool usage distribution across project."""
        tool_summary = stats_project.get_tool_usage_summary()
        
        # Day 1: 3 bash
        # Day 2: 1 each of str_replace_editor, bash, read
        # Day 3: no tools
        assert tool_summary.get("bash", 0) == 4
        assert tool_summary.get("str_replace_editor", 0) == 1
        assert tool_summary.get("read", 0) == 1

    def test_daily_cost_pattern(self, stats_project):
        """Test analyzing daily cost patterns."""
        sessions_by_day = {}
        for session in stats_project.sessions:
            day = session.start_time.day
            sessions_by_day[day] = session.total_cost
        
        # Verify increasing daily costs
        assert sessions_by_day[1] == pytest.approx(0.03, rel=1e-3)
        assert sessions_by_day[2] == pytest.approx(0.06, rel=1e-3)
        assert sessions_by_day[3] == pytest.approx(0.09, rel=1e-3)


class TestProjectErrorHandling:
    """Test error handling in Project operations."""

    def test_empty_project_properties(self):
        """Test properties on empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_project_path = Path(tmpdir) / "empty"
            empty_project_path.mkdir()
            
            project = load_project(str(empty_project_path))
            
            assert project.total_sessions == 0
            assert project.total_messages == 0
            assert project.total_cost == 0.0
            assert project.total_duration == timedelta(0)
            assert project.get_tool_usage_summary() == {}

    def test_filter_with_no_matches(self, project_dir):
        """Test filter_sessions with no matching sessions."""
        project = load_project(str(project_dir))
        
        # Filter for impossibly high cost
        expensive = project.filter_sessions(lambda s: s.total_cost > 1000)
        assert expensive == []

    def test_date_range_no_matches(self, project_dir):
        """Test get_sessions_by_date_range with no matches."""
        project = load_project(str(project_dir))
        
        # Search for future dates
        future_sessions = project.get_sessions_by_date_range(
            datetime(2025, 1, 1),
            datetime(2025, 12, 31)
        )
        assert future_sessions == []

    def test_most_expensive_with_n_greater_than_sessions(self, project_dir):
        """Test get_most_expensive_sessions with n > total sessions."""
        project = load_project(str(project_dir))
        
        # Ask for more sessions than exist
        top_sessions = project.get_most_expensive_sessions(n=100)
        assert len(top_sessions) == 3  # Should return all 3 sessions

    def test_project_with_corrupted_session(self):
        """Test project handling of corrupted session files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "corrupted_project"
            project_path.mkdir()
            
            # Good session
            good_session = project_path / "good.jsonl"
            with open(good_session, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "good",
                    "version": "1.0.0",
                    "cwd": str(project_path),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Good"}]
                    }
                }) + "\n")
            
            # Corrupted session
            bad_session = project_path / "bad.jsonl"
            with open(bad_session, "w") as f:
                f.write("{invalid json}\n")
            
            # Project should skip corrupted sessions
            project = load_project(str(project_path))
            assert len(project.sessions) == 1
            assert project.sessions[0].session_id == "good"