#!/usr/bin/env python3
"""Wrapper to import the Rust module and test Project class."""

import sys
import os

# Find the built library
lib_paths = [
    './target/release/librust_sdk.dylib',
    './target/release/librust_sdk.so',
    './target/debug/librust_sdk.dylib',
    './librust_sdk.dylib',
    './_core.so',
    './claude_sdk.so'
]

found = False
for path in lib_paths:
    if os.path.exists(path):
        print(f"Found library at: {path}")
        found = True
        break

if not found:
    print("Could not find the built library!")
    print("Searched in:", lib_paths)
    sys.exit(1)

# Import directly from the .so file
import importlib.util
spec = importlib.util.spec_from_file_location("_core", path)
claude_sdk = importlib.util.module_from_spec(spec)
sys.modules["_core"] = claude_sdk
spec.loader.exec_module(claude_sdk)

# Test basic import
print(f"Module loaded: {claude_sdk}")
print(f"Available functions: {[attr for attr in dir(claude_sdk) if not attr.startswith('_')]}")

# Test Project class
try:
    projects = claude_sdk.find_projects()
    print(f"\nFound {len(projects)} projects")
    
    if projects:
        print(f"\nLoading first project: {projects[0].name}")
        project = claude_sdk.load_project(projects[0])
        
        # Test properties
        print(f"Project name: {project.name}")
        print(f"Session count: {project.session_count}")
        print(f"Total cost: ${project.total_cost:.4f}")
        print(f"Total messages: {project.total_messages}")
        
        # Test methods
        if project.session_count > 0:
            # Test get_session
            first_session = project.sessions[0]
            found = project.get_session(first_session.session_id)
            print(f"\nget_session test: {'PASS' if found else 'FAIL'}")
            
            # Test filter_sessions
            filtered = project.filter_sessions(lambda s: s.total_cost > 0)
            print(f"filter_sessions test: Found {len(filtered)} sessions with cost > 0")
            
            # Test get_all_messages
            messages = project.get_all_messages()
            print(f"get_all_messages test: Found {len(messages)} total messages")
            
            # Test calculate_daily_costs
            daily = project.calculate_daily_costs()
            print(f"calculate_daily_costs test: Found costs for {len(daily)} days")
            
        print("\n✅ Project class working correctly!")
        
except Exception as e:
    print(f"\n❌ Error testing Project class: {e}")
    import traceback
    traceback.print_exc()