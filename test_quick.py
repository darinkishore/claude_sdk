import sys
sys.path.insert(0, '/Users/darin/Library/Python/3.13/lib/python/site-packages')
import claude_sdk

# Test Project
projects = claude_sdk.find_projects()
print(f'Found {len(projects)} projects')

if projects:
    project = claude_sdk.load_project(projects[0])
    print(f'\nProject: {project.name}')
    print(f'Has path attribute: {hasattr(project, "path")}')
    print(f'Session count: {project.session_count}')
    print(f'Total cost: ${project.total_cost:.4f}')
    
    # Test methods
    if project.sessions:
        first = project.sessions[0]
        found = project.get_session(first.session_id)
        print(f'\nget_session works: {found is not None}')
        
        expensive = project.get_most_expensive_sessions(3)
        print(f'get_most_expensive_sessions works: {len(expensive)} sessions')
        
        daily = project.calculate_daily_costs()
        print(f'calculate_daily_costs works: {len(daily)} days')
        
        all_msgs = project.get_all_messages()
        print(f'get_all_messages works: {len(all_msgs)} messages')
        
        print(f'\nProject repr: {repr(project)}')