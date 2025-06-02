#!/usr/bin/env python3
"""
Session export examples for Claude SDK.

This script demonstrates how to export session data to JSON format
for analysis, archival, or integration with other tools.
"""

import claude_sdk
import json
from pathlib import Path
from datetime import datetime


def export_to_json(session, output_path="session_export.json", include_full_content=True):
    """Export session to JSON format."""
    print(f"\n=== Exporting to JSON: {output_path} ===")
    
    export_data = {
        "session_id": session.session_id,
        "exported_at": datetime.now().isoformat(),
        "metadata": {
            "total_messages": len(session.messages),
            "total_cost": session.total_cost,
            "duration_seconds": session.duration,
            "tools_used": list(session.tools_used),
            "project_name": session.project_name,
            "conversation_stats": {
                "max_depth": session.conversation_tree.max_depth(),
                "branches": session.conversation_tree.count_branches(),
                "orphaned_messages": len(session.conversation_tree.orphaned_messages)
            }
        },
        "messages": []
    }
    
    for msg in session.messages:
        message_data = {
            "uuid": msg.uuid,
            "parent_uuid": msg.parent_uuid,
            "role": msg.role,
            "timestamp": msg.timestamp,
            "model": msg.model,
            "cost": msg.cost,
            "tokens": {
                "total": msg.total_tokens or 0,
                "input": msg.input_tokens or 0,
                "output": msg.output_tokens or 0
            },
            "tools": msg.tools,
            "is_sidechain": msg.is_sidechain
        }
        
        if include_full_content:
            message_data["text"] = msg.text
            
            # Include tool details
            if msg.has_tool_use():
                message_data["tool_uses"] = []
                for tool_block in msg.get_tool_blocks():
                    message_data["tool_uses"].append({
                        "id": tool_block.id,
                        "name": tool_block.name,
                        "input": tool_block.input
                    })
        else:
            # Just include preview
            message_data["text_preview"] = msg.text[:200] + "..." if len(msg.text) > 200 else msg.text
        
        export_data["messages"].append(message_data)
    
    # Add tool execution details
    if session.tool_executions:
        export_data["tool_executions"] = []
        for exec in session.tool_executions:
            exec_data = {
                "tool_name": exec.tool_name,
                "timestamp": exec.timestamp,
                "duration_ms": exec.duration_ms,
                "success": exec.is_success(),
                "input": exec.input
            }
            
            if include_full_content:
                exec_data["output"] = {
                    "content": exec.output.content,
                    "stdout": exec.output.stdout,
                    "stderr": exec.output.stderr,
                    "is_error": exec.output.is_error
                }
            
            export_data["tool_executions"].append(exec_data)
    
    # Add conversation tree structure
    export_data["conversation_structure"] = export_conversation_tree(session.conversation_tree)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported {len(session.messages)} messages to {output_path}")
    print(f"  File size: {Path(output_path).stat().st_size / 1024:.1f} KB")
    
    return export_data


def export_conversation_tree(tree):
    """Export conversation tree structure."""
    def node_to_dict(node):
        return {
            "message_uuid": node.message.uuid,
            "role": node.message.role,
            "text_preview": node.message.text[:100] + "..." if len(node.message.text) > 100 else node.message.text,
            "children": [node_to_dict(child) for child in node.children]
        }
    
    return {
        "roots": [node_to_dict(root) for root in tree.root_messages],
        "stats": {
            "total_messages": tree.stats.total_messages,
            "max_depth": tree.stats.max_depth,
            "leaf_count": tree.stats.leaf_count,
            "branches": tree.stats.num_branches
        },
        "orphaned_messages": list(tree.orphaned_messages),
        "circular_references": list(tree.circular_references)
    }


def export_project_summary(project, output_dir="project_export"):
    """Export comprehensive project summary to JSON."""
    print(f"\n=== Exporting Project: {project.name} ===")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Project summary JSON
    summary_data = {
        'project_name': project.name,
        'exported_at': datetime.now().isoformat(),
        'total_sessions': len(project.sessions),
        'total_cost': project.total_cost,
        'total_messages': project.total_messages,
        'total_duration_hours': project.total_duration / 3600 if project.total_duration else None,
        'tool_usage': dict(project.tool_usage_count),
        'sessions': []
    }
    
    # Add session summaries
    for session in project.sessions:
        session_summary = {
            'session_id': session.session_id,
            'messages': len(session.messages),
            'cost': session.total_cost,
            'duration_minutes': session.duration / 60 if session.duration else None,
            'tools': list(session.tools_used),
            'conversation_depth': session.conversation_tree.max_depth(),
            'branches': session.conversation_tree.count_branches(),
            'timestamp': session.messages[0].timestamp if session.messages else None
        }
        summary_data['sessions'].append(session_summary)
    
    # Sort sessions by timestamp
    summary_data['sessions'].sort(key=lambda s: s['timestamp'] or '', reverse=True)
    
    # Calculate additional insights
    if project.sessions:
        # Cost distribution
        costs = [s.total_cost for s in project.sessions]
        summary_data['cost_insights'] = {
            'average': sum(costs) / len(costs),
            'median': sorted(costs)[len(costs) // 2],
            'max': max(costs),
            'min': min(costs)
        }
        
        # Tool popularity
        tool_sessions = {}
        for session in project.sessions:
            for tool in session.tools_used:
                if tool not in tool_sessions:
                    tool_sessions[tool] = 0
                tool_sessions[tool] += 1
        
        summary_data['tool_popularity'] = {
            tool: {
                'total_uses': project.tool_usage_count.get(tool, 0),
                'sessions_used': count,
                'percentage_of_sessions': count / len(project.sessions) * 100
            }
            for tool, count in tool_sessions.items()
        }
    
    # Write project summary
    summary_path = output_path / "project_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"✓ Exported project summary to {summary_path}")
    
    # Export individual sessions (summaries only)
    sessions_dir = output_path / "session_summaries"
    sessions_dir.mkdir(exist_ok=True)
    
    for i, session in enumerate(project.sessions):
        session_file = sessions_dir / f"{session.session_id}_summary.json"
        export_to_json(session, session_file, include_full_content=False)
    
    print(f"✓ Exported {len(project.sessions)} session summaries to {sessions_dir}")
    
    return output_path


def export_analysis_data(sessions, output_path="analysis_export.json"):
    """Export data optimized for analysis tools."""
    print(f"\n=== Exporting Analysis Data ===")
    
    analysis_data = {
        'exported_at': datetime.now().isoformat(),
        'session_count': len(sessions),
        'sessions': [],
        'aggregated_metrics': {
            'total_cost': 0,
            'total_messages': 0,
            'total_tokens': 0,
            'tool_usage': {},
            'model_usage': {},
            'hourly_distribution': {str(h): 0 for h in range(24)}
        }
    }
    
    for session in sessions:
        # Session data for analysis
        session_data = {
            'session_id': session.session_id,
            'start_time': session.messages[0].timestamp if session.messages else None,
            'duration_seconds': session.duration,
            'cost': session.total_cost,
            'message_count': len(session.messages),
            'tools_used': list(session.tools_used),
            'conversation_depth': session.conversation_tree.max_depth(),
            'branch_count': session.conversation_tree.count_branches(),
            'messages_by_role': {
                'user': len(session.get_messages_by_role('user')),
                'assistant': len(session.get_messages_by_role('assistant'))
            }
        }
        
        # Token analysis
        total_tokens = sum(msg.total_tokens or 0 for msg in session.messages)
        session_data['total_tokens'] = total_tokens
        
        # Cost per message
        session_data['avg_cost_per_message'] = (
            session.total_cost / len(session.messages) 
            if session.messages else 0
        )
        
        # Tool execution stats
        if session.tool_executions:
            successful = sum(1 for e in session.tool_executions if e.is_success())
            session_data['tool_success_rate'] = successful / len(session.tool_executions)
        else:
            session_data['tool_success_rate'] = None
        
        analysis_data['sessions'].append(session_data)
        
        # Update aggregated metrics
        analysis_data['aggregated_metrics']['total_cost'] += session.total_cost
        analysis_data['aggregated_metrics']['total_messages'] += len(session.messages)
        analysis_data['aggregated_metrics']['total_tokens'] += total_tokens
        
        # Tool usage
        for tool in session.tools_used:
            if tool not in analysis_data['aggregated_metrics']['tool_usage']:
                analysis_data['aggregated_metrics']['tool_usage'][tool] = 0
            analysis_data['aggregated_metrics']['tool_usage'][tool] += 1
        
        # Model usage
        for msg in session.messages:
            if msg.model:
                if msg.model not in analysis_data['aggregated_metrics']['model_usage']:
                    analysis_data['aggregated_metrics']['model_usage'][msg.model] = 0
                analysis_data['aggregated_metrics']['model_usage'][msg.model] += 1
        
        # Hourly distribution
        for msg in session.messages:
            if msg.timestamp:
                try:
                    dt = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00'))
                    hour = str(dt.hour)
                    analysis_data['aggregated_metrics']['hourly_distribution'][hour] += 1
                except:
                    pass
    
    # Calculate derived metrics
    if analysis_data['session_count'] > 0:
        analysis_data['aggregated_metrics']['avg_cost_per_session'] = (
            analysis_data['aggregated_metrics']['total_cost'] / 
            analysis_data['session_count']
        )
        analysis_data['aggregated_metrics']['avg_messages_per_session'] = (
            analysis_data['aggregated_metrics']['total_messages'] / 
            analysis_data['session_count']
        )
    
    with open(output_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"✓ Exported analysis data to {output_path}")
    print(f"  Total sessions: {analysis_data['session_count']}")
    print(f"  Total cost: ${analysis_data['aggregated_metrics']['total_cost']:.2f}")
    
    return analysis_data


def main():
    """Run export examples."""
    print("Claude SDK Export Examples")
    print("=" * 50)
    
    # Find sessions
    sessions = claude_sdk.find_sessions()
    
    if not sessions:
        print("No sessions found.")
        return
    
    # Create exports directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    # Example 1: Export single session (full content)
    print("\n1. Exporting single session with full content...")
    latest_session_path = max(sessions[:10], key=lambda p: p.stat().st_mtime)
    session = claude_sdk.load(latest_session_path)
    
    export_to_json(session, export_dir / "session_full.json", include_full_content=True)
    
    # Example 2: Export session summary only
    print("\n2. Exporting session summary...")
    export_to_json(session, export_dir / "session_summary.json", include_full_content=False)
    
    # Example 3: Export project if available
    if session.project_name:
        print("\n3. Exporting project...")
        try:
            project = claude_sdk.load_project(session.project_name)
            export_project_summary(project, export_dir / f"project_{project.name}")
        except Exception as e:
            print(f"Could not export project: {e}")
    
    # Example 4: Export analysis data for multiple sessions
    print("\n4. Creating analysis export...")
    recent_sessions = []
    for session_path in sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            recent_sessions.append(claude_sdk.load(session_path))
        except Exception:
            continue
    
    if recent_sessions:
        export_analysis_data(recent_sessions, export_dir / "analysis_data.json")
    
    print(f"\n✅ All exports completed! Check the '{export_dir}' directory.")
    print("\nExported files are optimized for:")
    print("  • Data analysis in Python/R/Julia")
    print("  • Visualization tools")
    print("  • Custom reporting")
    print("  • Long-term archival")


if __name__ == "__main__":
    main()