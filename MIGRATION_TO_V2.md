# Migration Guide: Environment-Centric to Conversation-Centric API

## Overview

Version 2.0 introduces a cleaner separation of concerns:
- **Workspace**: Infrastructure (executor + observer)
- **Conversation**: Interaction management (owns transitions)

This eliminates the confusing `TransitionRecorder` and makes conversations first-class citizens.

## Key Changes

### 1. ClaudeEnvironment → Workspace

**Before:**
```rust
use claude_sdk::execution::ClaudeEnvironment;

let mut env = ClaudeEnvironment::new(workspace_path)?;
let transition = env.execute("Hello")?;
```

**After:**
```rust
use claude_sdk::execution::{Workspace, Conversation};
use std::sync::Arc;

let workspace = Arc::new(Workspace::new(workspace_path)?);
let mut conv = Conversation::new(workspace);
let transition = conv.send("Hello")?;
```

### 2. Transitions are owned by Conversations

**Before:**
```rust
// Transitions recorded globally per workspace
let history = env.history(Some(10))?;  // Last 10 transitions in workspace
```

**After:**
```rust
// Each conversation owns its transitions
let history = conv.history();  // All transitions in this conversation
```

### 3. No more continue_session flag

**Before:**
```rust
let t1 = env.execute("First message")?;
let t2 = env.execute_with_options("Continue", true)?;  // continue_session = true
```

**After:**
```rust
let t1 = conv.send("First message")?;
let t2 = conv.send("Continue")?;  // Automatically continues
```

### 4. Session ID management is automatic

**Before:**
```rust
let prompt = ClaudePrompt {
    text: "Hello".to_string(),
    continue_session: false,
    resume_session_id: Some(session_id),  // Manual tracking
};
```

**After:**
```rust
conv.send("Hello")?;  // Session IDs tracked internally
```

## Migration Examples

### Simple Script

**Before:**
```rust
let mut env = ClaudeEnvironment::new(workspace)?;
let t1 = env.start("Create a file")?;
let t2 = env.continue_session("Add content")?;
println!("Cost: ${}", t1.execution.cost + t2.execution.cost);
```

**After:**
```rust
let workspace = Arc::new(Workspace::new(workspace)?);
let mut conv = Conversation::new(workspace);
conv.send("Create a file")?;
conv.send("Add content")?;
println!("Cost: ${}", conv.total_cost());
```

### Multiple Conversations

**Before:**
```rust
// Not well supported - transitions intermingle
let env = Arc::new(Mutex::new(ClaudeEnvironment::new(workspace)?));
let conv1 = env.lock().unwrap().new_conversation();
let conv2 = env.lock().unwrap().new_conversation();
```

**After:**
```rust
// Clean separation
let workspace = Arc::new(Workspace::new(workspace)?);
let mut conv1 = Conversation::new(workspace.clone());
let mut conv2 = Conversation::new(workspace.clone());
// Each conversation maintains its own history
```

### Tool Permissions

**Before:**
```rust
let mut executor = ClaudeExecutor::new(workspace)?;
executor.set_allowed_tools(Some("Read,Write".to_string()));
```

**After:**
```rust
// Still set on executor, accessed through workspace
let mut workspace = Workspace::new(workspace_path)?;
workspace.executor.set_allowed_tools(Some("Read,Write".to_string()));
```

## Benefits

1. **Clearer mental model**: Conversations are first-class objects
2. **Better isolation**: Each conversation tracks its own history
3. **Simpler API**: No manual session ID tracking
4. **Future-proof**: Can add conversation features (fork, replay, etc.)

## Backward Compatibility

The old API is deprecated but still available:

```rust
#[allow(deprecated)]
use claude_sdk::execution::ClaudeEnvironment;

// This still works but shows deprecation warning
let env = ClaudeEnvironment::new(workspace)?;
```

## Next Steps

1. Update imports to use `Workspace` and `Conversation`
2. Refactor code to create conversations explicitly  
3. Remove manual session ID tracking
4. Enjoy the cleaner API!