#!/usr/bin/env python3
"""
Basic usage examples for the Claude SDK.

This script demonstrates fundamental operations like loading sessions,
accessing messages, and extracting basic statistics.
"""

import claude_sdk
from pathlib import Path


def main():
    # Example 1: Load a session file
    print("=== Loading a Session ===")
    
    # You can use either a string path or Path object
    session_path = "~/.claude/projects/myproject/session_20240101_120000.jsonl"
    
    try:
        session = claude_sdk.load(session_path)
        print(f"✓ Loaded session: {session.session_id}")
        print(f"  Messages: {len(session.messages)}")
        print(f"  Cost: ${session.total_cost:.4f}")
        print(f"  Duration: {session.duration / 60:.1f} minutes" if session.duration else "  Duration: Unknown")
    except FileNotFoundError:
        print(f"✗ Session file not found: {session_path}")
        print("  Using example path - replace with your actual session file")
    except claude_sdk.ParseError as e:
        print(f"✗ Failed to parse session: {e}")
    
    # Example 2: Find all sessions
    print("\n=== Finding Sessions ===")
    
    sessions = claude_sdk.find_sessions()
    print(f"Found {len(sessions)} total sessions")
    
    # Show first 5 sessions
    for i, session_path in enumerate(sessions[:5]):
        print(f"  {i+1}. {session_path.name}")
    
    if len(sessions) > 5:
        print(f"  ... and {len(sessions) - 5} more")
    
    # Example 3: Find sessions for a specific project
    print("\n=== Project-Specific Sessions ===")
    
    # Try to use the first available project if any exist
    available_projects = claude_sdk.find_projects()
    project_name = available_projects[0].name if available_projects else "myproject"
    project_sessions = claude_sdk.find_sessions(project=project_name)
    
    if project_sessions:
        print(f"Found {len(project_sessions)} sessions in project '{project_name}'")
        
        # Load and analyze the most recent session
        if project_sessions:
            latest_session_path = max(project_sessions, key=lambda p: p.stat().st_mtime)
            latest_session = claude_sdk.load(latest_session_path)
            
            print(f"\nLatest session in '{project_name}':")
            print(f"  ID: {latest_session.session_id}")
            print(f"  Messages: {len(latest_session.messages)}")
            print(f"  Tools used: {', '.join(latest_session.tools_used) or 'None'}")
    else:
        print(f"No sessions found for project '{project_name}'")
    
    # Example 4: Load and analyze a project
    print("\n=== Loading a Complete Project ===")
    
    try:
        # Load project by name
        project = claude_sdk.load_project(project_name)
        
        print(f"Project: {project.name}")
        print(f"  Total sessions: {len(project.sessions)}")
        print(f"  Total cost: ${project.total_cost:.2f}")
        print(f"  Total messages: {project.total_messages}")
        
        # Show tool usage
        print("\n  Tool usage across all sessions:")
        for tool, count in sorted(project.tool_usage_count.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {tool}: {count} uses")
            
    except FileNotFoundError:
        print(f"Project '{project_name}' not found")
        
        # Show available projects
        available_projects = claude_sdk.find_projects()
        if available_projects:
            print("\nAvailable projects:")
            for proj_path in available_projects[:5]:
                print(f"  - {proj_path.name}")
    
    # Example 5: Basic message iteration
    print("\n=== Iterating Through Messages ===")
    
    if sessions:
        # Load the first available session for demonstration
        first_session = claude_sdk.load(sessions[0])
        
        print(f"First 3 messages from session {first_session.session_id}:")
        for i, message in enumerate(first_session.messages[:3]):
            preview = message.text[:80].replace('\n', ' ')
            if len(message.text) > 80:
                preview += "..."
            print(f"\n  Message {i+1} ({message.role}):")
            print(f"    {preview}")
            if message.tools:
                print(f"    Tools used: {', '.join(message.tools)}")
            if message.cost:
                print(f"    Cost: ${message.cost:.6f}")


if __name__ == "__main__":
    main()