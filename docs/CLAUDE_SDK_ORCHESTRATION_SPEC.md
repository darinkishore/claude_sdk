# Claude SDK Orchestration Specification

## Overview

This document captures the evolution of the Claude SDK from a pure JSONL parser (T0) to a full orchestration engine (T1) that enables programmatic control and optimization of Claude Code.

## The Journey: From Observation to Orchestration

### The Initial Insight

Our journey began with observing claude-trace and recognizing that Claude Code already provides programmatic interfaces:

```bash
claude --output-format json "Build a function"
claude --output-format stream-json "Fix the tests"
claude --continue "Now add error handling"
```

This led to a key realization: **Claude Code is a primitive** - a reliable, tool-using AI that we can orchestrate programmatically.

### The Orchestration Vision

Instead of trying to replace or wrap Claude Code, we recognized that the real opportunity is to:

1. **Be a really good Claude Code user, programmatically**
2. **Learn optimal usage patterns from experience**
3. **Enable DSPy and similar frameworks to optimize Claude's behavior**

The analogy: Claude Code is like a skilled programmer, and we're building the technical lead that knows what to tell the programmer to do next.

## Core Design Principles

### 1. Claude-Native Concepts

We deliberately chose terminology that reflects what's actually happening:

- **ClaudePrompt** - What we send to Claude (not "action")
- **ClaudeExecution** - What Claude did (not "response")
- **EnvironmentSnapshot** - The state of files and session (not abstract "state")
- **Transition** - A complete interaction cycle

### 2. Unopinionated Intelligence, Opinionated Mechanics

The SDK is opinionated about HOW to:
- Execute prompts via Claude CLI
- Observe environment changes
- Record transitions for learning

The SDK is NOT opinionated about:
- How to generate prompts (that's DSPy's job)
- How to evaluate success (user-defined)
- How to decompose tasks (learned behavior)

### 3. Progressive Disclosure

Simple usage:
```python
env = ClaudeEnvironment("./project")
transition = env.execute("Build a TODO app")
```

Advanced usage:
```python
# Full control over observation and execution
before = env.observer.snapshot()
execution = env.executor.run(ClaudePrompt(text, continue_session=True))
after = env.observer.snapshot()
transition = Transition(before, prompt, execution, after)
```

## Architecture

### The Transition: Fundamental Unit of Learning

```python
Transition = {
    before: EnvironmentSnapshot,    # What was true before
    prompt: ClaudePrompt,           # What we asked Claude
    execution: ClaudeExecution,     # What Claude did
    after: EnvironmentSnapshot,     # What was true after
}
```

This captures everything needed to learn from experience:
- What situation led to what prompt?
- What was the outcome?
- What changed in the environment?

### Environment Snapshots

A snapshot captures two sources of truth:

1. **File System State** - What actually exists on disk
2. **Session State** - Claude's conversation and context

```python
EnvironmentSnapshot = {
    files: Dict[Path, str],        # Current file contents
    session: Session,              # Parsed from JSONL (all messages)
    timestamp: DateTime,           # When captured
}
```

### Why This Design

1. **Snapshots over Streaming**: Complete state at discrete moments is simpler and sufficient
2. **Transitions as First-Class**: These are what we learn from
3. **Session Parsing Reuse**: T0 infrastructure handles JSONL parsing
4. **No Reward Assumptions**: Users/DSPy define what "good" means

## Integration with DSPy

The SDK provides the mechanics, DSPy provides the intelligence:

```python
@dspy.Module
class ClaudeOrchestrator:
    def __init__(self, env: ClaudeEnvironment):
        self.env = env
        self.prompt_gen = dspy.ChainOfThought("goal, snapshot -> prompt")
        
    def forward(self, goal: str) -> List[Transition]:
        transitions = []
        while not self.is_complete(goal):
            snapshot = self.env.observer.snapshot()
            prompt = self.prompt_gen(goal=goal, snapshot=snapshot).prompt
            transition = self.env.execute(prompt)
            transitions.append(transition)
        return transitions
```

## What We're Building (T1)

### Core Components

1. **ClaudeExecutor** - Wraps Claude CLI with JSON output
2. **EnvironmentObserver** - Snapshots files and session state  
3. **TransitionRecorder** - Stores transitions for learning
4. **ClaudeEnvironment** - Orchestrates the above

### What T1 Enables

- **Single Claude Orchestration**: Programmatic control with learning
- **DSPy Integration**: Natural interface for optimization
- **Experience Replay**: Learn from successful sessions
- **Cost-Aware Execution**: Track and optimize for cost

### What We're Deferring

- **Parallel Claudes**: Requires worktree management
- **Streaming State Updates**: Current design uses snapshots
- **Built-in Reward Functions**: Users define success

## The Bigger Picture

This SDK makes Claude Code a first-class citizen in the emerging ecosystem of AI orchestration:

1. **For Researchers**: Clean abstractions for studying AI agents
2. **For Engineers**: Powerful automation with learning
3. **For DSPy Users**: Natural integration with optimization

We're not building an agent framework - we're building the substrate that makes Claude Code orchestratable by ANY framework.

## Implementation Priorities

1. Verify JSONL updates during execution (critical assumption)
2. Build minimal T1 with core components
3. Create Python bindings with clean API
4. Demonstrate DSPy integration
5. Document patterns (MDP, HTN architectures)

## Success Criteria

The SDK succeeds if:

1. Users can programmatically control Claude Code
2. DSPy can optimize Claude's behavior over time
3. The abstractions feel natural, not forced
4. Common patterns (retry, error recovery) are simple
5. Advanced patterns (RL, planning) are possible

## Conclusion

We're making Claude Code programmable in the deepest sense - not just executable, but learnable and optimizable. The SDK provides the mechanics; frameworks like DSPy provide the intelligence; users provide the goals.

The result: Claude Code becomes a primitive that gets better at your specific tasks over time.