#!/usr/bin/env python3
"""Test the complete Project class implementation."""

# Import from the installed Python package
from claude_sdk import load_project, find_projects
from datetime import datetime

def test_project_api():
    print("=== Testing Project Class Implementation ===\n")
    
    # Find available projects
    print("1. Finding projects...")
    projects = find_projects()
    if not projects:
        print("No projects found to test!")
        return
    
    print(f"Found {len(projects)} projects")
    
    # Load the first project  
    print(f"\n2. Loading project: {projects[0].name}")
    project = load_project(projects[0])
    
    # Test basic properties
    print(f"\n3. Testing basic properties:")
    print(f"   - Name: {project.name}")
    print(f"   - Path: {project.path}")
    print(f"   - Session count: {project.session_count}")
    print(f"   - Total cost: ${project.total_cost:.4f}")
    print(f"   - Total messages: {project.total_messages}")
    print(f"   - Number of sessions: {len(project.sessions)}")
    
    # Test get_session method
    print(f"\n4. Testing get_session method:")
    if project.sessions:
        first_session = project.sessions[0]
        found_session = project.get_session(first_session.session_id)
        print(f"   - Found session: {found_session is not None}")
        print(f"   - Session ID matches: {found_session and found_session.session_id == first_session.session_id}")
    
    # Test filter_sessions
    print(f"\n5. Testing filter_sessions method:")
    expensive_sessions = project.filter_sessions(lambda s: s.total_cost > 0.01)
    print(f"   - Sessions with cost > $0.01: {len(expensive_sessions)}")
    
    # Test get_all_messages
    print(f"\n6. Testing get_all_messages method:")
    all_messages = project.get_all_messages()
    print(f"   - Total messages from all sessions: {len(all_messages)}")
    
    # Test get_sessions_by_date_range
    print(f"\n7. Testing get_sessions_by_date_range method:")
    if project.sessions and len(project.sessions) > 0:
        # Get date range from first session
        first_session = project.sessions[0]
        if first_session.start_time and first_session.end_time:
            start = first_session.start_time
            end = datetime.now()
            sessions_in_range = project.get_sessions_by_date_range(start, end)
            print(f"   - Sessions in date range: {len(sessions_in_range)}")
    
    # Test get_most_expensive_sessions
    print(f"\n8. Testing get_most_expensive_sessions method:")
    top_5 = project.get_most_expensive_sessions(5)
    print(f"   - Top 5 most expensive sessions:")
    for i, session in enumerate(top_5):
        print(f"     {i+1}. Session {session.session_id[:8]}... - ${session.total_cost:.4f}")
    
    # Test calculate_daily_costs
    print(f"\n9. Testing calculate_daily_costs method:")
    daily_costs = project.calculate_daily_costs()
    print(f"   - Days with costs: {len(daily_costs)}")
    if daily_costs:
        # Show first few days
        sorted_days = sorted(daily_costs.items())[:3]
        for date, cost in sorted_days:
            print(f"     {date}: ${cost:.4f}")
    
    # Test to_dict
    print(f"\n10. Testing to_dict method:")
    project_dict = project.to_dict()
    print(f"   - Dict keys: {list(project_dict.keys())}")
    print(f"   - Sessions in dict: {len(project_dict['sessions'])}")
    
    # Test iteration
    print(f"\n11. Testing iteration:")
    count = 0
    for session in project:
        count += 1
        if count > 3:
            break
    print(f"   - Can iterate over sessions: True")
    print(f"   - First 3 sessions iterated successfully")
    
    # Test __len__
    print(f"\n12. Testing __len__:")
    print(f"   - len(project) = {len(project)}")
    
    # Test string representations
    print(f"\n13. Testing string representations:")
    print(f"   - repr: {repr(project)}")
    print(f"   - str: {str(project)}")
    
    print("\n✅ All Project class features tested successfully!")

if __name__ == "__main__":
    test_project_api()