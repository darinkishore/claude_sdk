# Claude SDK Limitations and Known Issues

This document tracks known limitations, caveats, and design decisions in the Claude SDK.

## T1 Execution Engine Limitations

### 1. Tool Extraction from Cloned Transitions

**Issue**: `conversation.tools_used()` returns an empty vector.

**Cause**: 
- `ParsedSession` doesn't implement `Clone`
- When transitions are stored in conversations, they're cloned
- Cloning sets `session: None` to avoid expensive deep copies
- Without session data, tool extraction fails

**Workaround**: Extract tools directly from transitions before they're cloned:
```rust
// Works - direct access to transition
let transition = env.execute("Create a file")?;
let tools = transition.tool_executions(); // ✓ Works

// Doesn't work - after storing in conversation
let tools = conversation.tools_used(); // ✗ Returns empty
```

**Status**: Accepted limitation. May revisit if it becomes a user issue.

### 2. No Parallel Execution Support

**Issue**: The SDK doesn't support running multiple Claude executions in parallel within the same workspace.

**Cause**: 
- Claude's `--continue` behavior with concurrent sessions is undefined
- File system conflicts when multiple processes write to the same workspace
- Session tracking assumes sequential execution

**Impact**: Users must execute prompts sequentially.

**Status**: By design for T1. T2 orchestration layer may address this using worktrees.

### 3. Session ID Behavior

**Issue**: Claude creates a new session ID for every execution, even with `--continue`.

**Impact**: 
- Can't use session ID to track conversation continuity
- Must use our own conversation ID for tracking

**Status**: This is Claude's behavior, not a bug. The SDK correctly handles this.

### 4. Response Content for Tool-Only Executions

this is a bug. 
**Issue**: When Claude only uses tools without text output, the response is "(no content)".
 need to fix these.

### 5. Permission Requirements

**Issue**: `--dangerously-skip-permissions` must be accepted interactively before use.

**Impact**: Tests and automated workflows need to use `--allowedTools` instead.

**Status**: This is a Claude security feature. The SDK uses `--allowedTools` by default.

note: this is a bug too. if we accept it once interactively it should go away globally UNLESS claude team pushes a lovely update that resets it.


## T0 Parser Limitations

### 1. Large Session Files

**Issue**: Parsing very large JSONL files loads everything into memory.

**Impact**: Could cause memory issues with extremely long sessions.

**Status**: Acceptable for normal use cases. 

## General Architecture Limitations

### 1. Single Workspace per Environment

**Issue**: Each `ClaudeEnvironment` instance is tied to one workspace.

**Impact**: Managing multiple projects requires multiple environment instances.

**Status**: By design.

### 2. No Streaming Support

**Issue**: The SDK uses snapshots rather than streaming updates.

**Status**: Intentional design choice for simplicity.

its bascially realtime though, like literal microsecond delays.


## Python Binding Limitations

*To be documented as we implement Python bindings*

## Future Considerations

These limitations inform the design of T2 (orchestration layer):
- Parallel execution via worktrees
- Streaming execution monitoring
- Enhanced tool tracking
- Session management strategies



also,
uh... idk lmao pls report bugs



ooh also
i need to go in and manually inspect basically all the python stuff bc that is currecntly not done.

i dont think we're exposing the full parsed JSON when it comes to realtime execution; this is bc of a cloning bug i think.

also some other python TODOs are left in the current state of the repo. thats ok for now though.

lmao

this will likley have a bug or two fyi but it is a very good start; solid, the plumbing is complete and there are not tooooo many bugs.

i intend to use this quite a bit, so hopefully that will help . let us pray

---




Last updated: 2025-06-03
