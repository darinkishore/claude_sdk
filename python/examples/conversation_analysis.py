#!/usr/bin/env python3
"""
Conversation analysis examples for Claude SDK.

This script demonstrates how to analyze conversation structure,
including branching, sidechains, message threading, and conversation flow.
"""

import claude_sdk
from collections import defaultdict


def visualize_conversation_tree(tree, max_depth=5):
    """Create a visual representation of the conversation tree."""
    print("\n=== Conversation Tree Visualization ===")
    
    def print_node(node, prefix="", is_last=True, depth=0):
        if depth > max_depth:
            return
            
        # Create connection characters
        connector = "└── " if is_last else "├── "
        
        # Format message preview
        msg = node.message
        role_icon = "👤" if msg.role == "user" else "🤖"
        preview = msg.text[:50].replace('\n', ' ')
        if len(msg.text) > 50:
            preview += "..."
        
        # Print the node
        print(f"{prefix}{connector}{role_icon} {preview}")
        
        # Prepare prefix for children
        extension = "    " if is_last else "│   "
        child_prefix = prefix + extension
        
        # Print children
        for i, child in enumerate(node.children):
            is_last_child = i == len(node.children) - 1
            print_node(child, child_prefix, is_last_child, depth + 1)
    
    # Print stats first
    stats = tree.stats
    print(f"Tree statistics:")
    print(f"  Total messages: {stats.total_messages}")
    print(f"  Max depth: {stats.max_depth}")
    print(f"  Leaf nodes: {stats.leaf_count}")
    print(f"  Branches: {stats.num_branches}")
    
    if tree.orphaned_messages:
        print(f"  ⚠️  Orphaned messages: {len(tree.orphaned_messages)}")
    
    if tree.circular_references:
        print(f"  ⚠️  Circular references detected: {len(tree.circular_references)}")
    
    # Print the tree
    print("\nConversation flow:")
    for i, root in enumerate(tree.root_messages):
        is_last = i == len(tree.root_messages) - 1
        print_node(root, "", is_last)
        if not is_last:
            print()  # Empty line between trees


def analyze_conversation_structure(session):
    """Analyze the structure of a conversation."""
    print(f"\n=== Conversation Structure Analysis: {session.session_id} ===")
    
    tree = session.conversation_tree
    
    # Basic metrics
    print(f"Total messages: {len(session.messages)}")
    print(f"Main chain messages: {len(session.get_main_chain())}")
    sidechain_count = sum(1 for msg in session.messages if msg.is_sidechain)
    print(f"Sidechain messages: {sidechain_count}")
    
    # Branching analysis
    branch_points = []
    
    def find_branches(node, path=[]):
        current_path = path + [node.message.uuid]
        
        if len(node.children) > 1:
            branch_points.append({
                'node': node,
                'depth': len(current_path),
                'branches': len(node.children)
            })
        
        for child in node.children:
            find_branches(child, current_path)
    
    for root in tree.root_messages:
        find_branches(root)
    
    if branch_points:
        print(f"\nBranch points: {len(branch_points)}")
        for i, branch in enumerate(branch_points[:5], 1):  # Show first 5
            msg = branch['node'].message
            preview = msg.text[:60].replace('\n', ' ') + "..."
            print(f"  {i}. Depth {branch['depth']}, {branch['branches']} branches")
            print(f"     Message: {preview}")
    
    # Message role patterns
    print("\nMessage patterns:")
    role_sequence = [msg.role for msg in session.messages]
    
    # Count consecutive messages by same role
    consecutive_same_role = 0
    max_consecutive = 0
    prev_role = None
    
    for role in role_sequence:
        if role == prev_role:
            consecutive_same_role += 1
            max_consecutive = max(max_consecutive, consecutive_same_role)
        else:
            consecutive_same_role = 1
        prev_role = role
    
    print(f"  Max consecutive messages by same role: {max_consecutive}")
    
    # Conversation pace (messages per minute)
    if session.duration and session.duration > 0:
        messages_per_minute = len(session.messages) / (session.duration / 60)
        print(f"  Average pace: {messages_per_minute:.1f} messages/minute")
    
    # Depth analysis
    depths = []
    
    def calculate_depths(node, depth=0):
        depths.append(depth)
        for child in node.children:
            calculate_depths(child, depth + 1)
    
    for root in tree.root_messages:
        calculate_depths(root)
    
    if depths:
        avg_depth = sum(depths) / len(depths)
        print(f"  Average conversation depth: {avg_depth:.1f}")


def analyze_message_threading(session):
    """Analyze message threading and relationships."""
    print(f"\n=== Message Threading Analysis ===")
    
    # Build parent-child mapping
    children_by_parent = defaultdict(list)
    messages_by_uuid = {msg.uuid: msg for msg in session.messages}
    
    for msg in session.messages:
        if msg.parent_uuid:
            children_by_parent[msg.parent_uuid].append(msg)
    
    # Find messages with multiple children (branch points)
    branch_messages = [(uuid, children) for uuid, children in children_by_parent.items() 
                      if len(children) > 1]
    
    if branch_messages:
        print(f"Found {len(branch_messages)} branch points:")
        for uuid, children in branch_messages[:5]:  # Show first 5
            parent_msg = messages_by_uuid.get(uuid)
            if parent_msg:
                preview = parent_msg.text[:60].replace('\n', ' ') + "..."
                print(f"\n  Branch at: {preview}")
                print(f"  Branches into {len(children)} paths:")
                for i, child in enumerate(children, 1):
                    child_preview = child.text[:50].replace('\n', ' ')
                    print(f"    {i}. {child_preview}...")
    
    # Analyze thread lengths
    print("\n=== Thread Length Analysis ===")
    
    # Find all leaf messages (no children)
    leaf_messages = [msg for msg in session.messages 
                    if msg.uuid not in children_by_parent]
    
    thread_lengths = []
    for leaf in leaf_messages:
        # Trace back to root
        length = 1
        current = leaf
        while current.parent_uuid and current.parent_uuid in messages_by_uuid:
            length += 1
            current = messages_by_uuid[current.parent_uuid]
        thread_lengths.append(length)
    
    if thread_lengths:
        avg_length = sum(thread_lengths) / len(thread_lengths)
        max_length = max(thread_lengths)
        print(f"Number of conversation threads: {len(thread_lengths)}")
        print(f"Average thread length: {avg_length:.1f} messages")
        print(f"Longest thread: {max_length} messages")
    
    # Find orphaned messages
    orphaned = [msg for msg in session.messages 
               if msg.parent_uuid and msg.parent_uuid not in messages_by_uuid 
               and msg.parent_uuid != ""]
    
    if orphaned:
        print(f"\n⚠️  Found {len(orphaned)} orphaned messages (missing parents)")


def analyze_conversation_dynamics(session):
    """Analyze conversation dynamics and interaction patterns."""
    print(f"\n=== Conversation Dynamics ===")
    
    # Message length analysis
    user_lengths = [len(msg.text) for msg in session.get_messages_by_role("user")]
    assistant_lengths = [len(msg.text) for msg in session.get_messages_by_role("assistant")]
    
    if user_lengths and assistant_lengths:
        print("Message length statistics:")
        print(f"  User messages:")
        print(f"    Average: {sum(user_lengths)/len(user_lengths):.0f} chars")
        print(f"    Max: {max(user_lengths)} chars")
        print(f"  Assistant messages:")
        print(f"    Average: {sum(assistant_lengths)/len(assistant_lengths):.0f} chars")
        print(f"    Max: {max(assistant_lengths)} chars")
    
    # Response patterns
    print("\nResponse patterns:")
    
    # Calculate response times (based on message order, not actual time)
    response_pairs = []
    for i in range(len(session.messages) - 1):
        if (session.messages[i].role == "user" and 
            session.messages[i+1].role == "assistant"):
            response_pairs.append((session.messages[i], session.messages[i+1]))
    
    print(f"  User-Assistant pairs: {len(response_pairs)}")
    
    # Analyze tool usage in responses
    tool_responses = [pair for pair in response_pairs 
                     if pair[1].has_tool_use()]
    
    if tool_responses:
        tool_response_rate = len(tool_responses) / len(response_pairs) * 100
        print(f"  Responses with tool use: {tool_response_rate:.1f}%")
    
    # Conversation phases (based on message density)
    if len(session.messages) >= 10:
        print("\nConversation phases:")
        
        # Divide conversation into thirds
        third_size = len(session.messages) // 3
        phases = [
            ("Beginning", session.messages[:third_size]),
            ("Middle", session.messages[third_size:third_size*2]),
            ("End", session.messages[third_size*2:])
        ]
        
        for phase_name, phase_messages in phases:
            tool_count = sum(1 for msg in phase_messages if msg.has_tool_use())
            avg_length = sum(len(msg.text) for msg in phase_messages) / len(phase_messages)
            
            print(f"  {phase_name} ({len(phase_messages)} messages):")
            print(f"    Tool usage: {tool_count} messages")
            print(f"    Avg message length: {avg_length:.0f} chars")


def find_interesting_patterns(sessions):
    """Find interesting patterns across multiple sessions."""
    print("\n=== Cross-Session Conversation Patterns ===")
    
    # Collect statistics
    session_stats = []
    
    for session in sessions:
        tree = session.conversation_tree
        stats = {
            'session_id': session.session_id,
            'total_messages': len(session.messages),
            'max_depth': tree.max_depth(),
            'branches': tree.count_branches(),
            'sidechain_ratio': sum(1 for m in session.messages if m.is_sidechain) / len(session.messages) if session.messages else 0,
            'has_orphans': len(tree.orphaned_messages) > 0,
            'has_circular': len(tree.circular_references) > 0
        }
        session_stats.append(stats)
    
    # Find outliers
    avg_messages = sum(s['total_messages'] for s in session_stats) / len(session_stats)
    avg_depth = sum(s['max_depth'] for s in session_stats) / len(session_stats)
    
    print(f"Average session statistics across {len(sessions)} sessions:")
    print(f"  Messages per session: {avg_messages:.1f}")
    print(f"  Average max depth: {avg_depth:.1f}")
    
    # Complex conversations
    complex_sessions = [s for s in session_stats if s['branches'] > 5]
    if complex_sessions:
        print(f"\nHighly branched conversations: {len(complex_sessions)}")
        for stats in complex_sessions[:3]:
            print(f"  {stats['session_id']}: {stats['branches']} branch points")
    
    # Deep conversations
    deep_sessions = [s for s in session_stats if s['max_depth'] > avg_depth * 2]
    if deep_sessions:
        print(f"\nUnusually deep conversations: {len(deep_sessions)}")
        for stats in deep_sessions[:3]:
            print(f"  {stats['session_id']}: depth {stats['max_depth']}")
    
    # Sessions with issues
    problematic = [s for s in session_stats if s['has_orphans'] or s['has_circular']]
    if problematic:
        print(f"\nSessions with structural issues: {len(problematic)}")
        orphan_count = sum(1 for s in problematic if s['has_orphans'])
        circular_count = sum(1 for s in problematic if s['has_circular'])
        print(f"  With orphaned messages: {orphan_count}")
        print(f"  With circular references: {circular_count}")


def main():
    # Load sessions
    sessions = claude_sdk.find_sessions()
    
    if not sessions:
        print("No sessions found. Please ensure you have Claude Code sessions in ~/.claude/projects/")
        return
    
    # Example 1: Analyze a single session's structure
    print("Loading most recent session for structure analysis...")
    latest_session_path = max(sessions[:10], key=lambda p: p.stat().st_mtime)
    session = claude_sdk.load(latest_session_path)
    
    # Visualize the conversation tree
    visualize_conversation_tree(session.conversation_tree)
    
    # Analyze structure
    analyze_conversation_structure(session)
    
    # Analyze threading
    analyze_message_threading(session)
    
    # Analyze dynamics
    analyze_conversation_dynamics(session)
    
    # Example 2: Cross-session analysis
    print("\n" + "="*50)
    print("Loading multiple sessions for pattern analysis...")
    
    # Load up to 10 recent sessions
    recent_sessions = []
    for session_path in sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        try:
            recent_sessions.append(claude_sdk.load(session_path))
        except Exception as e:
            print(f"  Error loading {session_path.name}: {e}")
    
    if len(recent_sessions) >= 5:
        find_interesting_patterns(recent_sessions)


if __name__ == "__main__":
    main()