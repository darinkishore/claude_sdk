#!/usr/bin/env python3
"""
Test script to verify all examples run without errors.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_example(script_name, timeout=30):
    """Run an example script and return success status."""
    print(f"\n{'='*60}")
    print(f"Testing: {script_name}")
    print('='*60)
    
    env = os.environ.copy()
    env['NON_INTERACTIVE'] = '1'  # Skip interactive prompts
    
    try:
        # Run the script with output
        result = subprocess.run(
            [sys.executable, script_name],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        
        # Check for Python errors
        if result.returncode != 0:
            print(f"❌ Failed with exit code {result.returncode}")
            if result.stderr:
                print("Error output:")
                print(result.stderr[:500])
            return False
        
        # Check for actual Python exceptions (not just the word "Traceback" in output)
        if "Traceback (most recent call last):" in result.stderr:
            print("❌ Python exception detected in stderr")
            print(result.stderr[:500])
            return False
        
        # Also check stdout for unhandled exceptions
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if "Traceback (most recent call last):" in line:
                # Skip if it's part of displayed output (indented or prefixed)
                if line.strip() != "Traceback (most recent call last):":
                    continue
                # Make sure it's at the start of a line (actual traceback)
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("File "):
                    print("❌ Python exception detected in stdout")
                    return False
            
        print("✅ Completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False


def main():
    """Test all example scripts."""
    print("Claude SDK Examples Test Suite")
    print("="*60)
    
    # List of example scripts to test
    examples = [
        "basic_usage.py",
        "analyze_costs.py", 
        "tool_usage_analysis.py",
        "conversation_analysis.py",
        "export_sessions.py",
        "claude_wrapped.py"
    ]
    
    # Track results
    results = {}
    
    # Run each example
    for example in examples:
        if Path(example).exists():
            results[example] = run_example(example)
        else:
            print(f"\n⚠️  {example} not found")
            results[example] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for example, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{example:30} {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()