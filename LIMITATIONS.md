# Claude SDK Limitations and Known Issues

This document tracks known limitations, caveats, and design decisions in the Claude SDK.

## T1 Execution Engine Limitations

### 1. Tool Extraction from Cloned Transitions

This limitation has been resolved. `EnvironmentSnapshot` now stores the parsed
session inside an `Arc`, allowing transitions (and conversations) to be cloned
without losing session data. Tool extraction works correctly on stored
transitions and conversations.

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

**Issue**: When Claude only uses tools without text output, the response is "(no content)".

**Cause**: Claude's JSON response format returns this when there's no text output.

**Impact**: May be confusing but doesn't affect functionality.

**Status**: Working as designed.

### 5. Permission Requirements

**Issue**: `--dangerously-skip-permissions` must be accepted interactively before use.

**Impact**: Tests and automated workflows need to use `--allowedTools` instead.

**Status**: This is a Claude security feature. The SDK uses `--allowedTools` by default.

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

**Impact**: Can't observe Claude's execution in real-time.

**Status**: Intentional design choice for simplicity.

## Python Binding Limitations

*To be documented as we implement Python bindings*

## Future Considerations

These limitations inform the design of T2 (orchestration layer):
- Parallel execution via worktrees
- Streaming execution monitoring
- Enhanced tool tracking
- Session management strategies

---

Last updated: 2025-06-03