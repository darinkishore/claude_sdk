#!/usr/bin/env python3
"""Debug script to inspect Session and AgentResponse attributes."""

import claude_sdk
from pathlib import Path
import shutil

# Setup workspace
workspace = Path.home() / "test-claude-sdk-session"
workspace.mkdir(exist_ok=True)

# Create test file
test_file = workspace / "test.py"
test_file.write_text('print("test")\n')

# Create agent and send message
agent = claude_sdk.ClaudeAgent(workspace)
response = agent.send("What files are here?")

print("=" * 60)
print("AgentResponse attributes:")
print("=" * 60)
attrs = [attr for attr in dir(response) if not attr.startswith('_')]
for attr in sorted(attrs):
    try:
        value = getattr(response, attr)
        if callable(value):
            print(f"  {attr}() - method")
        else:
            print(f"  {attr} = {repr(value)[:100]}")
    except Exception as e:
        print(f"  {attr} - Error: {e}")

print("\n" + "=" * 60)
print("Session attributes:")
print("=" * 60)
session = response.session_after
if session:
    attrs = [attr for attr in dir(session) if not attr.startswith('_')]
    for attr in sorted(attrs):
        try:
            value = getattr(session, attr)
            if callable(value):
                print(f"  {attr}() - method")
            else:
                print(f"  {attr} = {repr(value)[:100]}")
        except Exception as e:
            print(f"  {attr} - Error: {e}")
            
    # Check metadata
    print("\n" + "=" * 60)
    print("SessionMetadata attributes:")
    print("=" * 60)
    metadata = session.metadata
    attrs = [attr for attr in dir(metadata) if not attr.startswith('_')]
    for attr in sorted(attrs):
        try:
            value = getattr(metadata, attr)
            print(f"  {attr} = {repr(value)[:100]}")
        except Exception as e:
            print(f"  {attr} - Error: {e}")

    # Check a message
    print("\n" + "=" * 60)
    print("Message attributes (first message):")
    print("=" * 60)
    if session.messages:
        msg = session.messages[0]
        attrs = [attr for attr in dir(msg) if not attr.startswith('_')]
        for attr in sorted(attrs):
            try:
                value = getattr(msg, attr)
                if callable(value):
                    print(f"  {attr}() - method")
                else:
                    print(f"  {attr} = {repr(value)[:100]}")
            except Exception as e:
                print(f"  {attr} - Error: {e}")
else:
    print("No session available!")

print("\n✅ Debug complete!")