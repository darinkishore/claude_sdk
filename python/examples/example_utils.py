#!/usr/bin/env python3
"""
Utility functions for Claude SDK examples.

This module provides helper functions to make examples more robust
and work reliably for any user, regardless of their data.
"""

import claude_sdk
import sys
import os
from pathlib import Path


def find_valid_sessions(limit=None, project=None):
    """Find valid, non-empty sessions."""
    all_sessions = claude_sdk.find_sessions(project=project)
    
    valid_sessions = []
    for session_path in all_sessions:
        try:
            # Check if file is not empty
            if session_path.stat().st_size > 0:
                # Try to load it to verify it's valid
                session = claude_sdk.load(session_path)
                if session.messages:  # Has actual messages
                    valid_sessions.append(session_path)
        except Exception:
            # Skip problematic sessions silently
            continue
        
        if limit and len(valid_sessions) >= limit:
            break
    
    return valid_sessions


def find_active_project():
    """Find a project with valid sessions."""
    projects = claude_sdk.find_projects()
    
    for project_path in projects:
        try:
            project = claude_sdk.load_project(project_path)
            if project.sessions:  # Has valid sessions
                return project
        except Exception:
            continue
    
    return None


def load_example_session():
    """Load a valid session for examples, or return None with helpful message."""
    valid_sessions = find_valid_sessions(limit=10)
    
    if not valid_sessions:
        print("\n⚠️  No valid Claude sessions found.")
        print("To use these examples, you need Claude Code sessions in ~/.claude/projects/")
        print("Run Claude Code and create some sessions first!")
        return None
    
    # Load the most recent valid session
    latest_session_path = max(valid_sessions, key=lambda p: p.stat().st_mtime)
    return claude_sdk.load(latest_session_path)


def load_example_project():
    """Load a valid project for examples, or return None with helpful message."""
    project = find_active_project()
    
    if not project:
        print("\n⚠️  No valid Claude projects found.")
        print("To use these examples, you need Claude Code projects in ~/.claude/projects/")
        return None
    
    return project


def safe_input(prompt, default=""):
    """Input that can be skipped in non-interactive mode."""
    # Check if running in non-interactive mode
    if not sys.stdin.isatty() or os.environ.get('CI') or os.environ.get('NON_INTERACTIVE'):
        print(f"{prompt} [Skipped - non-interactive mode]")
        return default
    
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\n[Input skipped]")
        return default


def format_cost(cost):
    """Format cost value safely."""
    if cost is None or cost == 0:
        return "$0.00"
    return f"${cost:.4f}"


def print_session_summary(session):
    """Print a nice summary of a session."""
    print(f"\nSession: {session.session_id}")
    print(f"  Messages: {len(session.messages)}")
    print(f"  Cost: {format_cost(session.total_cost)}")
    print(f"  Tools used: {', '.join(session.tools_used) or 'None'}")
    
    if session.duration:
        print(f"  Duration: {session.duration / 60:.1f} minutes")


def print_no_data_message(data_type="sessions"):
    """Print a helpful message when no data is available."""
    print(f"\n📊 No {data_type} available for analysis.")
    print(f"This example would show {data_type} analysis if you had Claude Code {data_type}.")
    print("\nTo get started:")
    print("1. Use Claude Code to create some sessions")
    print("2. Run this example again")
    print(f"\nExample output would include {data_type} statistics, patterns, and insights.")


def ensure_export_directory(dir_name="exports"):
    """Ensure export directory exists."""
    export_dir = Path(dir_name)
    export_dir.mkdir(exist_ok=True)
    return export_dir