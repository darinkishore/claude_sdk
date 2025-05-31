import json

messages = []
with open('/Users/darin/.claude/projects/-Users-darin-Projects-apply-model/e4803ec5-5f6a-4214-bcef-daeb844c4ee2.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            msg = json.loads(line)
            if msg.get('type') \!= 'summary':
                messages.append((msg.get('uuid'), msg.get('parentUuid')))

print(f"Total non-summary messages: {len(messages)}")

# Build a map
children = {}
for uuid, parent in messages:
    if parent:
        if parent not in children:
            children[parent] = []
        children[parent].append(uuid)

# Find max depth iteratively to avoid stack overflow
def find_max_depth():
    # Start from roots
    roots = [uuid for uuid, parent in messages if parent is None]
    print(f"Number of root messages: {len(roots)}")
    
    max_depth = 0
    stack = [(root, 0) for root in roots]
    
    while stack:
        uuid, depth = stack.pop()
        max_depth = max(max_depth, depth)
        
        if uuid in children:
            for child in children[uuid]:
                stack.append((child, depth + 1))
    
    return max_depth

max_depth = find_max_depth()
print(f"Maximum depth: {max_depth}")
