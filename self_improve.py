#!/usr/bin/env python3
"""
self_improve.py - Claude SDK Self-Improvement Demo

This script demonstrates the meta-programming capability of the Claude SDK
by having Claude use the SDK to add a feature to the SDK itself!

The feature being added: Configurable model selection
Currently the model is hardcoded to 'claude-sonnet-4-20250514' in the executor.

This script will:
1. Use the Claude SDK to load the SDK project
2. Ask Claude to implement configurable model selection
3. Show the results of Claude modifying its own codebase
"""

import os
import sys
from pathlib import Path

# Add the Python package to the path if running from source
sdk_root = Path(__file__).parent
python_path = sdk_root / "python"
if python_path.exists():
    sys.path.insert(0, str(python_path))

import claude_sdk


def main():
    """Run the self-improvement demonstration."""
    print("🤖 Claude SDK Self-Improvement Demo")
    print("=" * 50)
    print(f"Working directory: {sdk_root}")
    print()
    
    # Create an agent for the SDK project itself
    print("📦 Initializing Claude agent for self-improvement...")
    agent = claude_sdk.ClaudeAgent(str(sdk_root), auto_continue=True)
    
    # The prompt that will guide Claude to add the feature
    improvement_prompt = """
    I need you to add configurable model selection to this Claude SDK. 
    
    Currently the model is hardcoded in src/execution/executor.rs. Looking at the TODO.md file,
    this is a planned feature that needs implementation.
    
    Please implement the following:
    
    1. In src/execution/executor.rs:
       - Add an optional `model` field to ClaudeExecutor struct
       - Add a `set_model(&mut self, model: Option<String>)` method
       - Update the execute() method to only pass --model flag if model is set
       - Default should remain None (use Claude's default)
    
    2. In src/execution/workspace.rs:
       - Add a method to configure the model through Workspace
       - This should delegate to the executor's set_model
    
    3. In src/execution/conversation.rs:
       - Add model configuration option to Conversation
       - Thread it through to the workspace
    
    4. In src/python/classes.rs:
       - Expose model configuration in Python bindings for Workspace
       - Add Python method to set the model
    
    5. In python/claude_sdk/agent.py:
       - Add a `model` parameter to ClaudeAgent.__init__ with default None
       - Pass it through to the underlying Workspace
    
    Make sure to follow the existing code patterns and style. The model parameter should
    be optional everywhere, defaulting to None which means "use claude sonnet 4, like we currently do rn".
    
    Implement this feature now, making all necessary changes across the codebase.

    When you're done, commit your changes to the repo.

    Read the files first! Then, think, use your TODOs tool, finally, make a plan, then implement.
    """
    
    print("🚀 Sending self-improvement request to Claude...")
    print("\nPrompt summary: Add configurable model selection to the SDK")
    print("-" * 50)
    
    # Execute the self-improvement
    response = agent.send(improvement_prompt)
    
    # Display results
    print("\n✅ Self-improvement complete!")
    print("-" * 50)
    print(f"📝 Claude's response: {response.text[:200]}..." if len(response.text) > 200 else response.text)
    print(f"\n📊 Execution metrics:")
    print(f"   - Cost: ${response.cost:.4f}")
    print(f"   - Duration: {response.duration_ms}ms")
    print(f"   - Tools used: {len(response.tools_used)} ({', '.join(response.tools_used[:3])}...)" if len(response.tools_used) > 3 else f"   - Tools used: {response.tools_used}")
    
    print(f"\n📁 Files modified ({len(response.files_modified)}):")
    for file in response.files_modified[:10]:  # Show first 10
        print(f"   - {file}")
    if len(response.files_modified) > 10:
        print(f"   ... and {len(response.files_modified) - 10} more")
    
    print(f"\n📁 Files created ({len(response.files_created)}):")
    for file in response.files_created[:5]:  # Show first 5
        print(f"   - {file}")
    
    if response.has_errors:
        print("\n⚠️  Some tools reported errors during execution")
    
    print("\n🎉 The Claude SDK has successfully used itself to add a new feature!")
    print("   You can now use the 'model' parameter when creating ClaudeAgent instances.")
    
    # Save the conversation for analysis
    conversation_path = sdk_root / "self_improvement_session.json"
    agent.save_conversation(str(conversation_path))
    print(f"\n💾 Conversation saved to: {conversation_path}")
    
    return response


if __name__ == "__main__":
    try:
        response = main()
    except Exception as e:
        print(f"\n❌ Error during self-improvement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)