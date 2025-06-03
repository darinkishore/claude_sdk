#!/usr/bin/env python3
"""Comprehensive example of Claude SDK usage.

This example demonstrates all major features of the Claude SDK:
- T0: Session parsing and analysis
- T1: Execution engine with high and low-level APIs
"""

import claude_sdk
from pathlib import Path
import json
import sys


def demo_session_parsing():
    """Demonstrate T0 session parsing features."""
    print("=== T0: Session Parsing ===\n")
    
    # Find sessions
    sessions = claude_sdk.find_sessions()
    print(f"Found {len(sessions)} total sessions")
    
    if sessions:
        # Load a recent session
        recent_session = sessions[-1]
        print(f"\nLoading session: {recent_session.name}")
        
        session = claude_sdk.load(str(recent_session))
        print(f"Session ID: {session.metadata.session_id}")
        print(f"Messages: {len(session.messages)}")
        print(f"Total cost: ${session.metadata.total_cost_usd:.4f}")
        print(f"Model: {session.metadata.model}")
        
        # Show tools used
        if session.metadata.tool_stats:
            print("\nTools used:")
            for tool, count in session.metadata.tool_stats.items():
                print(f"  - {tool}: {count} times")
    else:
        print("No sessions found. Run Claude to create some!")


def demo_high_level_api(workspace_path: str):
    """Demonstrate T1 high-level API."""
    print("\n\n=== T1: High-Level Execution API ===\n")
    
    # Create test file
    test_file = Path(workspace_path) / "calculator.py"
    test_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

print(add(5, 3))
""")
    print(f"Created test file: {test_file}")
    
    # Create agent
    agent = claude_sdk.ClaudeAgent(workspace_path)
    print(f"\nCreated agent for: {workspace_path}")
    
    # Send a message
    print("\nSending: 'Add type hints to calculator.py'")
    response = agent.send("Add type hints to calculator.py")
    
    print(f"\nResponse: {response.text or '(actions only)'}")
    print(f"Cost: ${response.cost:.4f}")
    print(f"Duration: {response.duration_ms}ms")
    print(f"Tools used: {response.tools_used}")
    print(f"Files modified: {response.files_modified}")
    
    # Continue conversation
    print("\n\nContinuing: 'Now add a docstring'")
    response2 = agent.send("Now add a docstring to the add function")
    print(f"Cost: ${response2.cost:.4f}")
    print(f"Total conversation cost: ${agent.total_cost:.4f}")
    
    # Show final file
    print(f"\nFinal file content:")
    print("-" * 40)
    print(test_file.read_text())
    print("-" * 40)
    
    # Save conversation
    save_path = Path(workspace_path) / "conversation.json"
    agent.save_conversation(save_path)
    print(f"\nSaved conversation to: {save_path}")
    
    return agent


def demo_low_level_api(workspace_path: str):
    """Demonstrate T1 low-level API."""
    print("\n\n=== T1: Low-Level Execution API ===\n")
    
    # Create workspace and conversation
    workspace = claude_sdk.Workspace(workspace_path)
    conversation = claude_sdk.Conversation(workspace, record=True)
    
    print(f"Created conversation: {conversation.id}")
    print(f"Session IDs: {conversation.session_ids}")
    
    # Create and send prompt
    prompt = claude_sdk.ClaudePrompt(
        "Create a simple README.md file",
        resume_session_id=None
    )
    
    print(f"\nSending prompt: '{prompt.text}'")
    transition = conversation.send(prompt.text)
    
    print(f"\nTransition details:")
    print(f"  - ID: {transition.id}")
    print(f"  - Response: {transition.execution.response or '(no text response)'}")
    print(f"  - Cost: ${transition.execution.cost:.4f}")
    print(f"  - Session ID: {transition.execution.session_id}")
    print(f"  - Tools used: {transition.tools_used()}")
    
    # Check what changed
    if Path(workspace_path, "README.md").exists():
        print(f"\n✅ README.md was created!")




def main():
    """Run all demonstrations."""
    print("=== Claude SDK Comprehensive Example ===\n")
    
    # Check for --execute flag
    execute = "--execute" in sys.argv
    
    if not execute:
        print("This example demonstrates Claude SDK features.")
        print("To actually execute Claude (costs money!), run with --execute flag.")
        print("\nShowing API examples only...\n")
    
    # Always show session parsing (read-only)
    demo_session_parsing()
    
    # Set up test workspace
    workspace = Path.home() / ".claude-sdk-demo"
    workspace.mkdir(exist_ok=True)
    print(f"\n\nUsing demo workspace: {workspace}")
    
    if execute:
        # Actually run Claude
        print("\n⚠️  Executing Claude commands - this will incur costs!")
        
        try:
            # High-level API demo
            agent = demo_high_level_api(str(workspace))
            
            # Low-level API demo  
            demo_low_level_api(str(workspace))
            
        except Exception as e:
            print(f"\n❌ Execution failed: {type(e).__name__}: {e}")
            print("\nMake sure:")
            print("1. Claude CLI is installed")
            print("2. You have API credits")
            print("3. The workspace directory is accessible")
    else:
        # Just show the APIs
        print("\n\n=== API Examples (not executed) ===")
        
        print("\nHigh-level API:")
        print("""
    agent = claude_sdk.ClaudeAgent("/your/project")
    response = agent.send("Build something cool")
    print(f"Cost: ${response.cost}")
    print(f"Files: {response.files_created}")
        """)
        
        print("\nLow-level API:")
        print("""
    workspace = claude_sdk.Workspace("/your/project")
    conversation = claude_sdk.Conversation(workspace)
    transition = conversation.send("Do something")
    print(f"Tools used: {transition.tools_used()}")
        """)
    
    # Cleanup note
    if execute:
        print(f"\n\nDemo files created in: {workspace}")
        print("You can safely delete this directory when done.")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()