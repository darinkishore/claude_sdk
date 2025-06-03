# Claude SDK Execution Troubleshooting

Common issues and solutions when using the T1 execution engine.

## "No session files found" Error

### Problem
```
RuntimeError: Workspace error: Observer error: No session files found
```

### Cause
This happens when Claude hasn't initialized a project in the directory you're working in. Claude needs to create project metadata at `~/.claude/projects/[encoded-path]/`.

### Solutions

1. **Use an existing project directory**
   ```python
   # Good - subdirectory of existing project
   agent = ClaudeAgent("/Users/you/myproject/.test")
   
   # Bad - system temp directory
   agent = ClaudeAgent("/tmp/test")  # Won't work!
   ```

2. **Initialize Claude in the directory first**
   ```bash
   cd /your/new/directory
   claude -p "Hello"  # Initialize Claude here
   ```

3. **Use a known working directory for tests**
   ```python
   # Create a test directory in your home folder
   test_dir = Path.home() / "claude-sdk-tests" / "test1"
   test_dir.mkdir(parents=True, exist_ok=True)
   agent = ClaudeAgent(str(test_dir))
   ```

## Empty Response Text

### Problem
```python
response = agent.send("Do something")
print(response.text)  # Prints nothing or "(no content)"
```

### Cause
Some Claude executions return empty text when they only use tools without generating a text response.

### Solution
Check what actually happened:
```python
print(f"Tools used: {response.tools_used}")
print(f"Files modified: {response.files_modified}")
print(f"Cost: ${response.cost}")  # If > 0, execution happened
```

## Path Encoding Issues

### Problem
Claude can't find the project directory even though it exists.

### Cause
Path encoding mismatch. Claude encodes paths in a specific way:
- `/path/to/project` → `-path-to-project`
- `/path/.hidden` → `-path--hidden`
- `/path/with_underscores` → `-path-with-underscores` (underscores become hyphens!)

### Solution
Check the actual encoded path:
```bash
ls ~/.claude/projects/ | grep yourproject
```

## Permission Errors

### Problem
Claude asks for permission to use tools during execution.

### Cause
The SDK uses default tool permissions. Currently, `skip_permissions` isn't exposed in Python bindings.

### Solution
The SDK uses Claude's default allowed tools (Read, Write, Edit, etc.). For now, permissions can't be customized from Python.

## Workspace Not Found

### Problem
```
RuntimeError: Workspace error: Observer error: Project not found
```

### Cause
The workspace directory doesn't exist or Claude hasn't been initialized there.

### Solution
```python
from pathlib import Path

# Ensure directory exists
workspace_path = Path("/your/workspace")
workspace_path.mkdir(parents=True, exist_ok=True)

# Then create agent
agent = ClaudeAgent(str(workspace_path))
```

## Slow First Execution

### Problem
The first execution in a new directory takes much longer than subsequent ones.

### Cause
Claude needs to initialize the project structure on first use.

### Solution
This is normal. Subsequent executions will be faster.

## Import Errors After Changes

### Problem
```
ImportError: cannot import name 'ClaudeAgent' from 'claude_sdk'
```

### Cause
Python extension needs rebuilding after Rust code changes.

### Solution
```bash
cd python
maturin develop
```

## Best Practices

1. **Test in real directories**: Always test in actual project directories, not temp folders
2. **Check costs**: Use `response.cost` to verify execution happened
3. **Monitor files**: Use `response.files_modified` to see what changed
4. **Save conversations**: Use `agent.save_conversation()` to debug issues later
5. **Use subdirectories**: Create `.claude-sdk-test/` subdirectories for testing

## Debug Checklist

When execution fails:

1. ✓ Is Claude CLI installed? (`which claude`)
2. ✓ Is the workspace a real directory? (not `/tmp/...`)
3. ✓ Does the directory exist? (`Path(workspace).exists()`)
4. ✓ Has Claude been initialized there? (`ls ~/.claude/projects/`)
5. ✓ Are you using the latest SDK? (`maturin develop`)
6. ✓ Check the full error traceback for clues

## Getting Help

If you're still stuck:
1. Check the [examples](../python/examples/) directory
2. Look at the test files for working examples
3. File an issue with the full error traceback