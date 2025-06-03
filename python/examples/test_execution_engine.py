#!/usr/bin/env python3
"""Test the T1 execution engine Python bindings."""

import claude_sdk
import tempfile
import os
from pathlib import Path

def test_basic_execution():
    """Test basic workspace and conversation functionality."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Testing in directory: {tmpdir}")
        
        # Create workspace
        workspace = claude_sdk.Workspace(tmpdir)
        print(f"✅ Created workspace at: {workspace.path}")
        
        # Create conversation
        conversation = claude_sdk.Conversation(workspace, record=True)
        print(f"✅ Created conversation with ID: {conversation.id}")
        
        # Check initial state
        print(f"Session IDs: {conversation.session_ids}")
        print(f"Total cost: ${conversation.total_cost}")
        print(f"History length: {len(conversation.history())}")
        
        # Test snapshot functionality
        try:
            snapshot = workspace.snapshot()
            print(f"✅ Workspace snapshot taken")
            print(f"  - Files: {len(snapshot.files)} files")
            print(f"  - Session ID: {snapshot.session_id}")
            print(f"  - Timestamp: {snapshot.timestamp}")
        except Exception as e:
            print(f"⚠️  Snapshot failed (expected if no Claude project): {e}")
        
        # Test ClaudePrompt creation
        prompt = claude_sdk.ClaudePrompt("Hello, world!")
        print(f"✅ Created prompt: '{prompt.text}'")
        print(f"  - Resume session ID: {prompt.resume_session_id}")
        
        # Test saving conversation (without actual execution)
        save_path = Path(tmpdir) / "conversation.json"
        try:
            conversation.save(str(save_path))
            print(f"✅ Saved conversation to: {save_path}")
        except Exception as e:
            print(f"⚠️  Save failed (expected with no transitions): {e}")

def test_environment_snapshot():
    """Test environment snapshot functionality."""
    print("\n--- Testing Environment Snapshot ---")
    
    # Create a test snapshot with mock data
    # Note: We can't create snapshots directly from Python, but we can inspect them
    # when returned from workspace operations
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("print('hello world')")
        
        workspace = claude_sdk.Workspace(tmpdir)
        print(f"✅ Created workspace with test file")
        
        # Try to get a snapshot (will fail without Claude project)
        try:
            snapshot = workspace.snapshot()
            print(f"  - Session file: {snapshot.session_file}")
            print(f"  - Files captured: {list(snapshot.files.keys())}")
        except Exception as e:
            print(f"  - Snapshot failed (expected): {type(e).__name__}")

def test_type_hierarchy():
    """Test that all expected types are available."""
    print("\n--- Testing Type Hierarchy ---")
    
    # T1 Execution types
    execution_types = [
        'Workspace',
        'Conversation', 
        'Transition',
        'ClaudePrompt',
        'ClaudeExecution',
        'EnvironmentSnapshot'
    ]
    
    for type_name in execution_types:
        if hasattr(claude_sdk, type_name):
            print(f"✅ {type_name} is available")
        else:
            print(f"❌ {type_name} is missing!")
    
    # Check that we can instantiate the basic types
    prompt = claude_sdk.ClaudePrompt("test", resume_session_id="abc123")
    print(f"✅ Created ClaudePrompt with resume_session_id: {prompt.resume_session_id}")

if __name__ == "__main__":
    print("=== Testing Claude SDK T1 Execution Engine ===\n")
    
    test_basic_execution()
    test_environment_snapshot()
    test_type_hierarchy()
    
    print("\n✅ All tests completed!")