"""Test utility functions for Rust bindings."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_sdk import find_sessions, find_projects, load_project, load, ParseError


class TestFindSessions:
    """Test find_sessions function."""

    @pytest.fixture
    def sessions_directory(self):
        """Create a directory structure with sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create project directories
            for proj_num in range(3):
                project_dir = base_path / f"project_{proj_num}"
                project_dir.mkdir()
                
                # Create sessions in each project
                for sess_num in range(2):
                    session_file = project_dir / f"session_{sess_num}.jsonl"
                    with open(session_file, "w") as f:
                        f.write(json.dumps({
                            "uuid": f"{proj_num:02d}{sess_num:02d}0000-0000-0000-0000-000000000001",
                            "timestamp": f"2024-01-{proj_num+1:02d}T{10+sess_num:02d}:00:00Z",
                            "type": "user",
                            "userType": "external",
                            "sessionId": f"proj{proj_num}-sess{sess_num}",
                            "version": "1.0.0",
                            "cwd": str(project_dir),
                            "isSidechain": False,
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": f"Project {proj_num} Session {sess_num}"}]
                            }
                        }) + "\n")
                
                # Add non-JSONL files that should be ignored
                (project_dir / "README.md").touch()
                (project_dir / "config.json").touch()
            
            # Create some files at root level (should be ignored)
            (base_path / "root_session.jsonl").touch()
            (base_path / "notes.txt").touch()
            
            yield base_path

    def test_find_sessions_basic(self, sessions_directory):
        """Test basic session discovery."""
        sessions = find_sessions(str(sessions_directory))
        
        # Should find 6 sessions (3 projects × 2 sessions each)
        assert len(sessions) == 6
        
        # All paths should be .jsonl files
        for session_path in sessions:
            assert session_path.endswith(".jsonl")
            assert "session_" in session_path

    def test_find_sessions_sorted(self, sessions_directory):
        """Test that sessions are sorted by path."""
        sessions = find_sessions(str(sessions_directory))
        
        # Convert to sorted list for comparison
        sorted_sessions = sorted(sessions)
        assert sessions == sorted_sessions

    def test_find_sessions_empty_directory(self):
        """Test finding sessions in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions = find_sessions(tmpdir)
            assert sessions == []

    def test_find_sessions_nonexistent_directory(self):
        """Test finding sessions in non-existent directory."""
        with pytest.raises(ParseError, match="not found"):
            find_sessions("/nonexistent/directory")

    def test_find_sessions_filters_correctly(self, sessions_directory):
        """Test that find_sessions only returns JSONL files in subdirectories."""
        sessions = find_sessions(str(sessions_directory))
        
        # Should not include root-level files
        assert not any("root_session.jsonl" in s for s in sessions)
        
        # Should not include non-JSONL files
        assert not any("README.md" in s for s in sessions)
        assert not any("config.json" in s for s in sessions)
        assert not any("notes.txt" in s for s in sessions)

    def test_find_sessions_nested_structure(self):
        """Test finding sessions in deeply nested structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create nested structure
            deep_path = base / "a" / "b" / "c"
            deep_path.mkdir(parents=True)
            
            session_file = deep_path / "nested.jsonl"
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "nested",
                    "version": "1.0.0",
                    "cwd": str(deep_path),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Nested session"}]
                    }
                }) + "\n")
            
            sessions = find_sessions(str(base))
            assert len(sessions) == 1
            assert "nested.jsonl" in sessions[0]


class TestFindProjects:
    """Test find_projects function."""

    @pytest.fixture
    def projects_directory(self):
        """Create a directory structure with projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create valid project directories (with sessions)
            for i in range(3):
                proj_dir = base_path / f"valid_project_{i}"
                proj_dir.mkdir()
                
                # Add at least one session to make it a valid project
                session_file = proj_dir / "session.jsonl"
                with open(session_file, "w") as f:
                    f.write(json.dumps({
                        "uuid": f"{i:02d}000000-0000-0000-0000-000000000001",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "type": "user",
                        "userType": "external",
                        "sessionId": f"project-{i}",
                        "version": "1.0.0",
                        "cwd": str(proj_dir),
                        "isSidechain": False,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": f"Project {i}"}]
                        }
                    }) + "\n")
            
            # Create empty directories (not valid projects)
            for i in range(2):
                empty_dir = base_path / f"empty_dir_{i}"
                empty_dir.mkdir()
            
            # Create files at root (should be ignored)
            (base_path / "file.txt").touch()
            (base_path / "data.jsonl").touch()
            
            yield base_path

    def test_find_projects_basic(self, projects_directory):
        """Test basic project discovery."""
        projects = find_projects(str(projects_directory))
        
        # Should only find directories with JSONL files
        assert len(projects) == 3
        
        # All should be valid project paths
        for project_path in projects:
            assert "valid_project_" in project_path
            assert Path(project_path).is_dir()

    def test_find_projects_sorted(self, projects_directory):
        """Test that projects are sorted by path."""
        projects = find_projects(str(projects_directory))
        
        sorted_projects = sorted(projects)
        assert projects == sorted_projects

    def test_find_projects_empty_directory(self):
        """Test finding projects in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            projects = find_projects(tmpdir)
            assert projects == []

    def test_find_projects_nonexistent_directory(self):
        """Test finding projects in non-existent directory."""
        with pytest.raises(ParseError, match="not found"):
            find_projects("/nonexistent/directory")

    def test_find_projects_filters_empty_dirs(self, projects_directory):
        """Test that find_projects excludes empty directories."""
        projects = find_projects(str(projects_directory))
        
        # Should not include empty directories
        assert not any("empty_dir" in p for p in projects)

    def test_find_projects_nested(self):
        """Test finding projects in nested structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create nested project structure
            nested_proj = base / "category" / "subcategory" / "project"
            nested_proj.mkdir(parents=True)
            
            # Add session to make it valid
            session_file = nested_proj / "work.jsonl"
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "nested-work",
                    "version": "1.0.0",
                    "cwd": str(nested_proj),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Nested project"}]
                    }
                }) + "\n")
            
            projects = find_projects(str(base))
            assert len(projects) == 1
            assert projects[0].endswith("project")


class TestLoadProject:
    """Test load_project function (already tested in test_project.py but adding edge cases)."""

    def test_load_project_with_symlinks(self):
        """Test loading project that contains symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create actual project
            real_project = base / "real_project"
            real_project.mkdir()
            
            # Create session
            session_file = real_project / "session.jsonl"
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "test",
                    "version": "1.0.0",
                    "cwd": str(real_project),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Test"}]
                    }
                }) + "\n")
            
            # Create symlink to project
            symlink_project = base / "symlink_project"
            symlink_project.symlink_to(real_project)
            
            # Should be able to load via symlink
            project = load_project(str(symlink_project))
            assert len(project.sessions) == 1

    def test_load_project_permission_error(self):
        """Test loading project with permission issues."""
        # This test is platform-specific and might not work everywhere
        # Skipping for now as it requires special permissions
        pytest.skip("Permission testing is platform-specific")


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple functions."""

    def test_find_and_load_workflow(self):
        """Test typical workflow: find projects, then load them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create multiple projects
            project_data = [
                ("python_project", 5, 0.05),
                ("rust_project", 3, 0.03),
                ("web_project", 8, 0.08),
            ]
            
            for proj_name, num_messages, cost_per_msg in project_data:
                proj_dir = base / proj_name
                proj_dir.mkdir()
                
                session_file = proj_dir / "main_session.jsonl"
                with open(session_file, "w") as f:
                    for i in range(num_messages):
                        # Alternate user/assistant
                        role = "user" if i % 2 == 0 else "assistant"
                        msg_type = "user" if i % 2 == 0 else "assistant"
                        
                        msg_data = {
                            "uuid": f"{proj_name[:4]}-{i:04d}-0000-0000-000000000001",
                            "parentUuid": f"{proj_name[:4]}-{i-1:04d}-0000-0000-000000000001" if i > 0 else None,
                            "timestamp": f"2024-01-01T{10+i:02d}:00:00Z",
                            "type": msg_type,
                            "sessionId": f"{proj_name}-session",
                            "version": "1.0.0",
                            "cwd": str(proj_dir),
                            "isSidechain": False,
                            "message": {
                                "role": role,
                                "content": [{"type": "text", "text": f"Message {i}"}]
                            }
                        }
                        
                        if role == "assistant":
                            msg_data["costUSD"] = cost_per_msg
                            msg_data["userType"] = "assistant"
                        else:
                            msg_data["userType"] = "external"
                        
                        f.write(json.dumps(msg_data) + "\n")
            
            # Find all projects
            project_paths = find_projects(str(base))
            assert len(project_paths) == 3
            
            # Load each project and verify
            total_cost = 0
            total_messages = 0
            
            for proj_path in project_paths:
                project = load_project(proj_path)
                total_cost += project.total_cost
                total_messages += project.total_messages
            
            # Verify aggregated stats
            # python: 2 assistant msgs * 0.05 = 0.10
            # rust: 1 assistant msg * 0.03 = 0.03
            # web: 4 assistant msgs * 0.08 = 0.32
            # Total: 0.45
            assert total_cost == pytest.approx(0.45, rel=1e-3)
            assert total_messages == 16  # 5 + 3 + 8

    def test_find_sessions_and_analyze(self):
        """Test finding all sessions and analyzing them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create projects with different tool usage patterns
            tools_by_project = {
                "bash_heavy": ["bash"] * 5,
                "editor_heavy": ["str_replace_editor"] * 3,
                "mixed_tools": ["bash", "str_replace_editor", "read", "bash"],
            }
            
            for proj_name, tools in tools_by_project.items():
                proj_dir = base / proj_name
                proj_dir.mkdir()
                
                session_file = proj_dir / "work.jsonl"
                with open(session_file, "w") as f:
                    for i, tool in enumerate(tools):
                        # User message
                        f.write(json.dumps({
                            "uuid": f"{proj_name[:4]}-{i*2:04d}-0000-0000-000000000001",
                            "parentUuid": f"{proj_name[:4]}-{i*2-2:04d}-0000-0000-000000000001" if i > 0 else None,
                            "timestamp": f"2024-01-01T{10+i:02d}:00:00Z",
                            "type": "user",
                            "userType": "external",
                            "sessionId": f"{proj_name}-session",
                            "version": "1.0.0",
                            "cwd": str(proj_dir),
                            "isSidechain": False,
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": f"Use {tool}"}]
                            }
                        }) + "\n")
                        
                        # Assistant with tool
                        f.write(json.dumps({
                            "uuid": f"{proj_name[:4]}-{i*2+1:04d}-0000-0000-000000000001",
                            "parentUuid": f"{proj_name[:4]}-{i*2:04d}-0000-0000-000000000001",
                            "timestamp": f"2024-01-01T{10+i:02d}:01:00Z",
                            "type": "assistant",
                            "sessionId": f"{proj_name}-session",
                            "version": "1.0.0",
                            "cwd": str(proj_dir),
                            "isSidechain": False,
                            "message": {
                                "role": "assistant",
                                "content": [
                                    {"type": "text", "text": f"Using {tool}"},
                                    {"type": "tool_use", "id": f"tool_{i}", "name": tool, "input": {}}
                                ]
                            }
                        }) + "\n")
            
            # Find all sessions
            session_paths = find_sessions(str(base))
            assert len(session_paths) == 3
            
            # Load and analyze tool usage
            total_tool_usage = {}
            for session_path in session_paths:
                session = load(session_path)
                for tool, count in session.tool_usage_summary.items():
                    total_tool_usage[tool] = total_tool_usage.get(tool, 0) + count
            
            # Verify tool counts
            assert total_tool_usage["bash"] == 7  # 5 + 2
            assert total_tool_usage["str_replace_editor"] == 4  # 3 + 1
            assert total_tool_usage["read"] == 1


class TestErrorRecovery:
    """Test error recovery and edge cases for utility functions."""

    def test_find_sessions_with_corrupted_files(self):
        """Test find_sessions handles corrupted JSONL files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create project with mix of good and bad files
            proj_dir = base / "mixed_project"
            proj_dir.mkdir()
            
            # Good session
            good_file = proj_dir / "good.jsonl"
            with open(good_file, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "good",
                    "version": "1.0.0",
                    "cwd": str(proj_dir),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Good"}]
                    }
                }) + "\n")
            
            # Corrupted file (should still be found by find_sessions)
            bad_file = proj_dir / "bad.jsonl"
            with open(bad_file, "w") as f:
                f.write("{invalid json}\n")
            
            # find_sessions should return both files
            sessions = find_sessions(str(base))
            assert len(sessions) == 2

    def test_unicode_in_paths(self):
        """Test handling of Unicode characters in paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create project with Unicode name
            unicode_proj = base / "项目_🚀_project"
            unicode_proj.mkdir()
            
            session_file = unicode_proj / "session.jsonl"
            with open(session_file, "w") as f:
                f.write(json.dumps({
                    "uuid": "00000000-0000-0000-0000-000000000001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "type": "user",
                    "userType": "external",
                    "sessionId": "unicode-test",
                    "version": "1.0.0",
                    "cwd": str(unicode_proj),
                    "isSidechain": False,
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": "Unicode test"}]
                    }
                }) + "\n")
            
            # Should handle Unicode paths correctly
            projects = find_projects(str(base))
            assert len(projects) == 1
            
            sessions = find_sessions(str(base))
            assert len(sessions) == 1
            
            # Should be able to load
            project = load_project(projects[0])
            assert len(project.sessions) == 1