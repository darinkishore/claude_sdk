#!/usr/bin/env python3
"""Simple test runner script."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the test suite."""
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "-x",  # Stop on first failure
        "--color=yes",  # Colored output
    ]
    
    print(f"Running tests from {tests_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())