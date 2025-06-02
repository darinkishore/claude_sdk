#!/usr/bin/env python3
"""
Advanced cost analysis for Claude SDK sessions.

This script provides deep insights into your Claude usage costs,
with fun comparisons, trends, and predictions.
"""

import claude_sdk
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import statistics
from pathlib import Path
import sys
import io

# Import utilities
try:
    from example_utils import (
        load_example_session, load_example_project, safe_input,
        ensure_export_directory, find_valid_sessions, print_no_data_message
    )
except ImportError:
    # Minimal fallbacks
    def load_example_session():
        sessions = claude_sdk.find_sessions()
        return claude_sdk.load(sessions[0]) if sessions else None
    
    def load_example_project():
        projects = claude_sdk.find_projects()
        return claude_sdk.load_project(projects[0]) if projects else None
    
    def ensure_export_directory(name="exports"):
        Path(name).mkdir(exist_ok=True)
        return Path(name)
    
    def print_no_data_message(data_type="data"):
        print(f"\n📊 No {data_type} available for analysis.")


# Cost comparisons
SUBSCRIPTION_COSTS = {
    'netflix': 15.49,
    'spotify': 10.99,
    'chatgpt_plus': 20.00,
    'github_copilot': 10.00,
    'youtube_premium': 13.99,
}

DAILY_ITEMS = {
    'coffee': 4.50,
    'lunch': 12.00,
    'subway_ride': 2.90,
    'newspaper': 2.50,
}


def format_cost(cost):
    """Format cost with appropriate precision."""
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def get_subscription_comparison(monthly_cost):
    """Compare monthly cost to popular subscriptions."""
    comparisons = []
    
    for service, price in sorted(SUBSCRIPTION_COSTS.items()):
        ratio = monthly_cost / price
        if ratio >= 1:
            comparisons.append(f"{ratio:.1f}x {service.replace('_', ' ').title()}")
        else:
            comparisons.append(f"{ratio:.1%} of {service.replace('_', ' ').title()}")
    
    return comparisons[:3]  # Top 3 comparisons


def get_daily_comparison(daily_cost):
    """Compare daily cost to common purchases."""
    for item, price in sorted(DAILY_ITEMS.items(), key=lambda x: x[1]):
        if daily_cost <= price * 1.2:
            ratio = daily_cost / price
            if ratio < 0.5:
                return f"Less than half a {item.replace('_', ' ')}"
            elif ratio < 1:
                return f"Almost a {item.replace('_', ' ')}"
            else:
                return f"About {ratio:.1f} {item.replace('_', ' ')}s"
    
    return f"A fancy dinner for one"


def analyze_cost_patterns(sessions):
    """Deep dive into cost patterns."""
    patterns = {
        'hourly': defaultdict(float),
        'daily': defaultdict(float),
        'weekly': defaultdict(float),
        'monthly': defaultdict(float),
        'by_model': defaultdict(float),
        'by_tool': defaultdict(float),
        'by_message_length': defaultdict(list),
    }
    
    for session in sessions:
        # Session-level patterns
        if session.messages and session.messages[0].timestamp:
            try:
                dt = datetime.fromisoformat(session.messages[0].timestamp.replace('Z', '+00:00'))
                patterns['hourly'][dt.hour] += session.total_cost
                patterns['daily'][dt.strftime('%A')] += session.total_cost
                patterns['weekly'][dt.isocalendar()[1]] += session.total_cost
                patterns['monthly'][dt.strftime('%Y-%m')] += session.total_cost
            except:
                pass
        
        # Message-level patterns
        for msg in session.messages:
            if msg.cost and msg.cost > 0:
                if msg.model:
                    patterns['by_model'][msg.model] += msg.cost
                
                # Cost by message length buckets
                length_bucket = (len(msg.text) // 1000) * 1000
                patterns['by_message_length'][length_bucket].append(msg.cost)
        
        # Tool costs
        for tool, cost in session.tool_costs.items():
            patterns['by_tool'][tool] += cost
    
    return patterns


def calculate_roi_metrics(sessions):
    """Calculate return on investment metrics."""
    total_cost = sum(s.total_cost for s in sessions)
    
    # Problems solved (sessions with successful tool executions)
    problems_solved = sum(
        1 for s in sessions 
        if any(exec.is_success() for exec in s.tool_executions)
    )
    
    # Code written (estimate from Write/Edit tools)
    code_operations = sum(
        1 for s in sessions 
        for exec in s.tool_executions 
        if exec.tool_name in ['Write', 'Edit', 'MultiEdit'] and exec.is_success()
    )
    
    # Ideas explored (branches in conversations)
    ideas_explored = sum(s.conversation_tree.count_branches() for s in sessions)
    
    # Knowledge gained (messages with learning/explanation)
    learning_messages = sum(
        1 for s in sessions 
        for msg in s.messages 
        if msg.role == 'assistant' and len(msg.text) > 500
    )
    
    return {
        'cost_per_problem': total_cost / problems_solved if problems_solved > 0 else 0,
        'cost_per_code_op': total_cost / code_operations if code_operations > 0 else 0,
        'cost_per_idea': total_cost / ideas_explored if ideas_explored > 0 else 0,
        'cost_per_learning': total_cost / learning_messages if learning_messages > 0 else 0,
        'problems_solved': problems_solved,
        'code_operations': code_operations,
        'ideas_explored': ideas_explored,
        'learning_messages': learning_messages,
    }


def generate_cost_insights(stats, patterns):
    """Generate interesting insights about costs."""
    insights = []
    
    # Most expensive hour
    if patterns['hourly']:
        peak_hour = max(patterns['hourly'].items(), key=lambda x: x[1])
        insights.append(f"Your most expensive hour is {peak_hour[0]}:00 ({format_cost(peak_hour[1])} total)")
    
    # Most expensive day
    if patterns['daily']:
        peak_day = max(patterns['daily'].items(), key=lambda x: x[1])
        insights.append(f"{peak_day[0]}s are your biggest investment days")
    
    # Model preferences
    if patterns['by_model']:
        top_model = max(patterns['by_model'].items(), key=lambda x: x[1])
        model_name = top_model[0].split('-')[1]  # Extract model name
        insights.append(f"You prefer {model_name.title()} models ({format_cost(top_model[1])} spent)")
    
    # Cost efficiency
    if stats.get('avg_cost_per_session', 0) > 0:
        if stats['avg_cost_per_session'] < 2:
            insights.append("You're a cost-efficient user! 💰")
        elif stats['avg_cost_per_session'] > 10:
            insights.append("You go deep with complex problems! 🚀")
    
    # Growth trend
    if patterns['monthly'] and len(patterns['monthly']) >= 3:
        monthly_costs = sorted(patterns['monthly'].items())
        recent_growth = monthly_costs[-1][1] / monthly_costs[-3][1] if monthly_costs[-3][1] > 0 else 1
        if recent_growth > 1.5:
            insights.append(f"Your usage is growing {(recent_growth-1)*100:.0f}% every 3 months")
    
    return insights


def create_cost_visualization(data, title, width=50):
    """Create ASCII bar chart for cost data."""
    if not data:
        return ""
    
    max_val = max(data.values())
    chart_lines = [f"\n{title}:"]
    
    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]:
        if max_val > 0:
            bar_length = int((value / max_val) * width)
            bar = "█" * bar_length
            chart_lines.append(f"{str(label)[:15]:>15} |{bar} {format_cost(value)}")
    
    return "\n".join(chart_lines)


def create_comprehensive_cost_report(sessions, projects):
    """Create a comprehensive cost analysis report."""
    # Basic stats
    total_cost = sum(s.total_cost for s in sessions)
    total_messages = sum(len(s.messages) for s in sessions)
    
    # Time-based analysis
    earliest_session = min(sessions, key=lambda s: s.messages[0].timestamp if s.messages else "")
    latest_session = max(sessions, key=lambda s: s.messages[0].timestamp if s.messages else "")
    
    if earliest_session.messages and latest_session.messages:
        try:
            start_date = datetime.fromisoformat(earliest_session.messages[0].timestamp.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(latest_session.messages[0].timestamp.replace('Z', '+00:00'))
            days_active = (end_date - start_date).days + 1
        except:
            days_active = 365  # Default to a year
    else:
        days_active = 365
    
    # Calculate averages
    daily_average = total_cost / days_active if days_active > 0 else 0
    monthly_average = daily_average * 30.44  # Average days per month
    
    # Get patterns
    patterns = analyze_cost_patterns(sessions)
    roi_metrics = calculate_roi_metrics(sessions)
    insights = generate_cost_insights({
        'total_cost': total_cost,
        'avg_cost_per_session': total_cost / len(sessions) if sessions else 0,
    }, patterns)
    
    # Create report
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_cost': total_cost,
            'total_sessions': len(sessions),
            'total_messages': total_messages,
            'days_active': days_active,
            'daily_average': daily_average,
            'monthly_average': monthly_average,
            'yearly_projection': daily_average * 365,
        },
        'comparisons': {
            'daily': get_daily_comparison(daily_average),
            'monthly_subscriptions': get_subscription_comparison(monthly_average),
            'yearly_equivalent': f"{total_cost / 12:.1f} months of ChatGPT Plus" if total_cost > 20 else "Less than a month of ChatGPT Plus",
        },
        'patterns': {
            'by_hour': dict(patterns['hourly']),
            'by_day': dict(patterns['daily']),
            'by_month': dict(patterns['monthly']),
            'by_model': dict(patterns['by_model']),
            'by_tool': dict(sorted(patterns['by_tool'].items(), key=lambda x: x[1], reverse=True)[:10]),
        },
        'roi_metrics': roi_metrics,
        'insights': insights,
        'top_sessions': [
            {
                'session_id': s.session_id,
                'cost': s.total_cost,
                'messages': len(s.messages),
                'tools_used': list(s.tools_used),
            }
            for s in sorted(sessions, key=lambda x: x.total_cost, reverse=True)[:5]
        ],
    }
    
    return report


def print_cost_summary(report):
    """Print an engaging cost summary."""
    print("\n" + "="*60)
    print("💰 CLAUDE COST ANALYSIS REPORT 💰".center(60))
    print("="*60)
    
    summary = report['summary']
    
    # Big numbers
    print(f"\n📊 Total Investment: {format_cost(summary['total_cost'])}")
    print(f"   Across {summary['total_sessions']} sessions over {summary['days_active']} days")
    
    # Daily breakdown
    print(f"\n📅 Daily Average: {format_cost(summary['daily_average'])}")
    print(f"   That's {report['comparisons']['daily']} per day")
    
    # Monthly comparison
    print(f"\n📱 Monthly Average: {format_cost(summary['monthly_average'])}")
    print("   Equivalent to:")
    for comp in report['comparisons']['monthly_subscriptions']:
        print(f"   • {comp}")
    
    # ROI metrics
    roi = report['roi_metrics']
    if roi['problems_solved'] > 0:
        print(f"\n🎯 Return on Investment:")
        print(f"   • {format_cost(roi['cost_per_problem'])} per problem solved")
        print(f"   • {roi['problems_solved']} total problems solved")
    
    if roi['code_operations'] > 0:
        print(f"   • {format_cost(roi['cost_per_code_op'])} per code operation")
        print(f"   • {roi['code_operations']} total code operations")
    
    # Patterns visualization
    if report['patterns']['by_tool']:
        print(create_cost_visualization(report['patterns']['by_tool'], "\n🛠️  Cost by Tool"))
    
    if len(report['patterns']['by_hour']) > 5:
        # Show top 5 hours
        top_hours = dict(sorted(report['patterns']['by_hour'].items(), 
                              key=lambda x: x[1], reverse=True)[:5])
        print(create_cost_visualization(top_hours, "\n⏰ Top 5 Most Expensive Hours"))
    
    # Insights
    if report['insights']:
        print("\n💡 Insights:")
        for insight in report['insights']:
            print(f"   • {insight}")
    
    # Projection
    yearly = summary['yearly_projection']
    print(f"\n🔮 Yearly Projection: {format_cost(yearly)}")
    print(f"   At current rate, that's {report['comparisons']['yearly_equivalent']}")
    
    print("\n" + "="*60)


def main():
    """Run comprehensive cost analysis."""
    print("Claude SDK Cost Analysis")
    print("="*50)
    
    # Suppress warnings
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Load all sessions
        all_sessions = []
        projects = claude_sdk.find_projects()
        
        if not projects:
            sys.stderr = original_stderr
            print("\n😕 No Claude projects found!")
            return
        
        print(f"\nFound {len(projects)} projects to analyze...")
        
        # Load sessions from all projects
        loaded_projects = 0
        for project_path in projects:
            try:
                project = claude_sdk.load_project(project_path)
                if project.sessions:
                    all_sessions.extend(project.sessions)
                    loaded_projects += 1
            except:
                continue
        
        sys.stderr = original_stderr
        print(f"Loaded {len(all_sessions)} sessions from {loaded_projects} projects")
        
    finally:
        sys.stderr = original_stderr
    
    if not all_sessions:
        print_no_data_message("sessions")
        return
    
    # Generate comprehensive report
    print("\nAnalyzing cost patterns...")
    report = create_comprehensive_cost_report(all_sessions, projects)
    
    # Print summary
    print_cost_summary(report)
    
    # Export full report
    export_dir = ensure_export_directory()
    report_path = export_dir / f"claude_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Full report exported to: {report_path}")
    
    # Quick actions
    print("\n🎯 Quick Actions:")
    print("   • Review your most expensive sessions in the exported report")
    print("   • Consider your peak hours for complex work")
    print("   • Compare your ROI metrics to optimize usage")
    print("\n✨ Happy analyzing!")


if __name__ == "__main__":
    main()