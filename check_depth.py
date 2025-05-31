import json

messages = []
with open('/Users/darin/.claude/projects/-Users-darin-Projects-apply-model/e4803ec5-5f6a-4214-bcef-daeb844c4ee2.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            msg = json.loads(line)
            messages.append((msg['uuid'], msg.get('parentUuid')))

# Build a map
children = {}
for uuid, parent in messages:
    if parent:
        if parent not in children:
            children[parent] = []
        children[parent].append(uuid)

# Find max depth
def find_depth(uuid, depth=0, visited=None):
    if visited is None:
        visited = set()
    if uuid in visited:
        return depth
    visited.add(uuid)
    
    if uuid not in children:
        return depth
    
    max_child_depth = depth
    for child in children[uuid]:
        child_depth = find_depth(child, depth + 1, visited)
        max_child_depth = max(max_child_depth, child_depth)
    
    return max_child_depth

# Find roots and their depths
roots = [uuid for uuid, parent in messages if parent is None]
print(f"Number of root messages: {len(roots)}")

max_depth = 0
for root in roots:
    depth = find_depth(root)
    max_depth = max(max_depth, depth)
    if depth > 10:
        print(f"Root {root} has depth {depth}")

print(f"Maximum depth: {max_depth}")
