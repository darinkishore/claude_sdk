#!/usr/bin/env python3
"""
Tool usage analysis examples for Claude SDK.

This script demonstrates how to analyze tool usage patterns,
execution times, success rates, and common tool combinations.
"""

import claude_sdk
from collections import defaultdict, Counter
from datetime import datetime
import statistics


def analyze_tool_executions(session):
    """Analyze tool execution patterns in a session."""
    print(f"\n=== Tool Execution Analysis: {session.session_id} ===")
    
    if not session.tool_executions:
        print("No tool executions found in this session.")
        return
    
    # Basic statistics
    print(f"Total tool executions: {len(session.tool_executions)}")
    
    # Success rate
    successful = sum(1 for exec in session.tool_executions if exec.is_success())
    success_rate = successful / len(session.tool_executions) * 100
    print(f"Success rate: {success_rate:.1f}% ({successful}/{len(session.tool_executions)})")
    
    # Tool frequency
    tool_counts = Counter(exec.tool_name for exec in session.tool_executions)
    print("\nTool usage frequency:")
    for tool, count in tool_counts.most_common():
        print(f"  {tool}: {count} times")
    
    # Execution times
    timed_executions = [exec for exec in session.tool_executions if exec.duration_ms]
    if timed_executions:
        print("\nExecution time statistics:")
        for tool in tool_counts:
            tool_times = [exec.duration_ms for exec in timed_executions 
                         if exec.tool_name == tool]
            if tool_times:
                avg_time = statistics.mean(tool_times)
                median_time = statistics.median(tool_times)
                max_time = max(tool_times)
                print(f"  {tool}:")
                print(f"    Average: {avg_time:.0f}ms")
                print(f"    Median: {median_time:.0f}ms")
                print(f"    Max: {max_time:.0f}ms")
    
    # Failed executions
    failed_execs = [exec for exec in session.tool_executions if not exec.is_success()]
    if failed_execs:
        print(f"\nFailed executions: {len(failed_execs)}")
        for exec in failed_execs[:5]:  # Show first 5
            error_msg = exec.output.stderr or exec.output.effective_content()
            error_preview = error_msg[:100] if error_msg else "No error message"
            print(f"  - {exec.tool_name}: {error_preview}")
    
    # Tool combinations (sequential patterns)
    print("\nCommon tool sequences:")
    sequences = []
    for i in range(len(session.tool_executions) - 1):
        curr_tool = session.tool_executions[i].tool_name
        next_tool = session.tool_executions[i + 1].tool_name
        sequences.append(f"{curr_tool} → {next_tool}")
    
    sequence_counts = Counter(sequences)
    for sequence, count in sequence_counts.most_common(5):
        if count > 1:  # Only show repeated patterns
            print(f"  {sequence}: {count} times")


def analyze_tool_usage_in_messages(session):
    """Analyze how tools are used within messages."""
    print(f"\n=== Tool Usage in Messages ===")
    
    # Messages with tools
    tool_messages = [msg for msg in session.messages if msg.has_tool_use()]
    print(f"Messages containing tool use: {len(tool_messages)}/{len(session.messages)} "
          f"({len(tool_messages)/len(session.messages)*100:.1f}%)")
    
    # Multiple tools in single message
    multi_tool_messages = [msg for msg in tool_messages if len(msg.tools) > 1]
    if multi_tool_messages:
        print(f"\nMessages with multiple tools: {len(multi_tool_messages)}")
        for msg in multi_tool_messages[:3]:  # Show first 3
            print(f"  - {', '.join(msg.tools)}")
    
    # Tool usage by message role
    print("\nTool usage by role:")
    for role in ["user", "assistant"]:
        role_messages = session.get_messages_by_role(role)
        role_tool_messages = [msg for msg in role_messages if msg.has_tool_use()]
        if role_messages:
            percentage = len(role_tool_messages) / len(role_messages) * 100
            print(f"  {role}: {len(role_tool_messages)}/{len(role_messages)} "
                  f"({percentage:.1f}%)")
    
    # Analyze specific tools
    for tool_name in session.tools_used[:5]:  # Top 5 tools
        tool_specific_messages = session.get_messages_by_tool(tool_name)
        if tool_specific_messages:
            print(f"\n'{tool_name}' tool analysis:")
            print(f"  Used in {len(tool_specific_messages)} messages")
            
            # Get tool blocks for detailed analysis
            total_invocations = 0
            example_inputs = []
            
            for msg in tool_specific_messages:
                tool_blocks = msg.get_tool_blocks()
                for block in tool_blocks:
                    if block.name == tool_name:
                        total_invocations += 1
                        if len(example_inputs) < 3 and block.input:
                            example_inputs.append(block.input)
            
            print(f"  Total invocations: {total_invocations}")
            
            # Show example inputs
            if example_inputs:
                print(f"  Example inputs:")
                for i, input_data in enumerate(example_inputs, 1):
                    # Format input preview
                    if isinstance(input_data, dict):
                        preview = str(input_data)[:100]
                    else:
                        preview = str(input_data)[:100]
                    print(f"    {i}. {preview}...")


def analyze_project_tool_patterns(project):
    """Analyze tool usage patterns across a project."""
    print(f"\n=== Project Tool Pattern Analysis: {project.name} ===")
    
    # Aggregate tool statistics
    all_executions = []
    tool_success_counts = defaultdict(lambda: {'success': 0, 'total': 0})
    tool_timing_data = defaultdict(list)
    
    for session in project.sessions:
        all_executions.extend(session.tool_executions)
        
        for exec in session.tool_executions:
            tool_success_counts[exec.tool_name]['total'] += 1
            if exec.is_success():
                tool_success_counts[exec.tool_name]['success'] += 1
            
            if exec.duration_ms:
                tool_timing_data[exec.tool_name].append(exec.duration_ms)
    
    print(f"Total tool executions across project: {len(all_executions)}")
    
    # Success rates by tool
    print("\nSuccess rates by tool:")
    for tool, counts in sorted(tool_success_counts.items()):
        success_rate = counts['success'] / counts['total'] * 100
        print(f"  {tool}: {success_rate:.1f}% "
              f"({counts['success']}/{counts['total']})")
    
    # Performance comparison
    print("\nPerformance statistics by tool:")
    for tool, times in sorted(tool_timing_data.items()):
        if len(times) >= 5:  # Only show tools with enough data
            p50 = statistics.median(times)
            p95 = sorted(times)[int(len(times) * 0.95)]
            print(f"  {tool}:")
            print(f"    Median (p50): {p50:.0f}ms")
            print(f"    95th percentile: {p95:.0f}ms")
            print(f"    Executions: {len(times)}")
    
    # Tool evolution over time
    print("\nTool usage evolution:")
    sessions_by_time = sorted(project.sessions, 
                            key=lambda s: s.messages[0].timestamp if s.messages else "")
    
    # Divide into quarters
    quarter_size = len(sessions_by_time) // 4 or 1
    quarters = [
        sessions_by_time[:quarter_size],
        sessions_by_time[quarter_size:quarter_size*2],
        sessions_by_time[quarter_size*2:quarter_size*3],
        sessions_by_time[quarter_size*3:]
    ]
    
    for i, quarter_sessions in enumerate(quarters, 1):
        tool_counts = Counter()
        for session in quarter_sessions:
            tool_counts.update(session.tools_used)
        
        if tool_counts:
            print(f"  Quarter {i} ({len(quarter_sessions)} sessions):")
            for tool, count in tool_counts.most_common(3):
                avg_per_session = count / len(quarter_sessions)
                print(f"    {tool}: {avg_per_session:.1f} uses/session")


def find_tool_patterns(sessions):
    """Find interesting patterns across multiple sessions."""
    print("\n=== Cross-Session Tool Patterns ===")
    
    # Common tool combinations across sessions
    session_toolsets = []
    for session in sessions:
        if session.tools_used:
            # Create a sorted tuple of tools for comparison
            toolset = tuple(sorted(session.tools_used))
            session_toolsets.append(toolset)
    
    toolset_counts = Counter(session_toolsets)
    
    print("Most common tool combinations:")
    for toolset, count in toolset_counts.most_common(10):
        if count > 1 and len(toolset) > 1:  # Only show repeated multi-tool patterns
            tools_str = ", ".join(toolset)
            print(f"  [{tools_str}]: {count} sessions")
    
    # Sessions with unusual tool usage
    all_tool_counts = Counter()
    for session in sessions:
        all_tool_counts.update(session.tools_used)
    
    # Find sessions using rare tools
    rare_tools = [tool for tool, count in all_tool_counts.items() if count <= 3]
    
    if rare_tools:
        print(f"\nRare tools (used in ≤3 sessions): {', '.join(rare_tools)}")
        
        print("\nSessions using rare tools:")
        for session in sessions[:100]:  # Check first 100 sessions
            session_rare_tools = [t for t in session.tools_used if t in rare_tools]
            if session_rare_tools:
                print(f"  {session.session_id}: {', '.join(session_rare_tools)}")


def main():
    # Load some sessions for analysis
    sessions = claude_sdk.find_sessions()
    
    if not sessions:
        print("No sessions found. Please ensure you have Claude Code sessions in ~/.claude/projects/")
        return
    
    # Example 1: Analyze tool executions in a single session
    print("Loading most recent session for tool analysis...")
    latest_session_path = max(sessions[:10], key=lambda p: p.stat().st_mtime)
    session = claude_sdk.load(latest_session_path)
    
    analyze_tool_executions(session)
    analyze_tool_usage_in_messages(session)
    
    # Example 2: Analyze project-wide patterns
    projects = claude_sdk.find_projects()
    if projects:
        print("\n" + "="*50)
        print("Loading first project for pattern analysis...")
        project = claude_sdk.load_project(projects[0])
        analyze_project_tool_patterns(project)
    
    # Example 3: Cross-session patterns
    print("\n" + "="*50)
    print("Loading multiple sessions for pattern discovery...")
    
    # Load up to 20 recent sessions
    recent_sessions = []
    for session_path in sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            recent_sessions.append(claude_sdk.load(session_path))
        except Exception as e:
            print(f"  Error loading {session_path.name}: {e}")
    
    if recent_sessions:
        find_tool_patterns(recent_sessions)


if __name__ == "__main__":
    main()