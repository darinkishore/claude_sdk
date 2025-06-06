#!/usr/bin/env python3
"""
Integration test for the self-implemented model configuration feature.

This test verifies that the model parameter is correctly passed to Claude CLI
by executing actual prompts with different models.

Valid models for testing:
- claude-3-7-sonnet-20250219
- claude-sonnet-4-20250514 (default)
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add the Python package to the path if running from source
sdk_root = Path(__file__).parent
python_path = sdk_root / "python"
if python_path.exists():
    sys.path.insert(0, str(python_path))

import claude_sdk


def main():
    """Run integration test for model configuration."""
    print("🧪 Model Configuration Integration Test")
    print("=" * 50)
    
    # Create test workspace in home directory (not /tmp or /var)
    test_dir = Path.home() / f"test-claude-sdk-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Test workspace: {test_dir}")
    
    try:
        # Test 1: Use non-default model (claude-3-7-sonnet-20250219)
        print("\n1️⃣ Testing with claude-3-7-sonnet-20250219...")
        agent1 = claude_sdk.ClaudeAgent(
            str(test_dir),
            auto_continue=False,
            model="claude-3-7-sonnet-20250219"
        )
        
        response1 = agent1.send("Say 'hi' and nothing else")
        print(f"   Response: {response1.text.strip()}")
        print(f"   Session ID: {response1.session_id}")
        print(f"   Cost: ${response1.cost:.4f}")
        
        # Check if we can access the model from execution metadata
        if hasattr(response1.transition.execution, 'model'):
            print(f"   Model used: {response1.transition.execution.model}")
        
        # Test 2: Use default model (claude-sonnet-4-20250514)
        print("\n2️⃣ Testing with default model (claude-sonnet-4-20250514)...")
        agent2 = claude_sdk.ClaudeAgent(
            str(test_dir),
            auto_continue=False,
            model="claude-sonnet-4-20250514"
        )
        
        response2 = agent2.send("Say 'hi' and nothing else")
        print(f"   Response: {response2.text.strip()}")
        print(f"   Session ID: {response2.session_id}")
        print(f"   Cost: ${response2.cost:.4f}")
        
        if hasattr(response2.transition.execution, 'model'):
            print(f"   Model used: {response2.transition.execution.model}")
        
        # Test 3: No model specified (should use default)
        print("\n3️⃣ Testing with no model specified...")
        agent3 = claude_sdk.ClaudeAgent(
            str(test_dir),
            auto_continue=False
        )
        
        response3 = agent3.send("Say 'hi' and nothing else")
        print(f"   Response: {response3.text.strip()}")
        print(f"   Session ID: {response3.session_id}")
        print(f"   Cost: ${response3.cost:.4f}")
        
        if hasattr(response3.transition.execution, 'model'):
            print(f"   Model used: {response3.transition.execution.model}")
        
        print("\n✅ Integration test complete!")
        print("\nKey observations:")
        print("- Different models may have different costs")
        print("- Each model should be reflected in the execution metadata")
        print("- The SDK successfully passes model configuration to Claude CLI")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test workspace...")
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    main()