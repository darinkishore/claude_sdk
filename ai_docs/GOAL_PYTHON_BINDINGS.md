# Goal: Python Bindings for Claude SDK T1 Execution

## Overview

This document defines the target Python API for the Claude SDK's T1 execution engine, with a focus on enabling DSPy integration and advanced orchestration patterns (RL/MDP, HTN).

## Current State

### What's Already Exposed (T0 Parser)
- `Session`, `Message`, `MessageRecord` - JSONL parsing
- `Project` - Multi-session projects  
- `load()`, `find_sessions()`, `find_projects()` - Discovery functions
- Various metadata and analysis types

### What's NOT Exposed (T1 Execution)
- `Workspace` - Execution context management
- `Conversation` - Sequential execution with transition history
- `Transition` - State change records (before/after snapshots + execution)
- `ClaudeExecutor`, `EnvironmentObserver` - Low-level execution components
- `ClaudePrompt`, `ClaudeExecution`, `EnvironmentSnapshot` - Core data types

### Critical Issues to Fix
1. **ParsedSession Clone**: Currently loses session data when cloning transitions
2. **TransitionRecorder Integration**: Exists but not used by Conversation
3. **Python Bindings**: No PyO3 bindings for T1 components

## Goal Architecture

### Core Design Principles
1. **Trace-Centric**: Transitions form traces that DSPy can learn from
2. **Progressive Disclosure**: Simple API for basic use, full access for advanced
3. **DSPy-Native**: Natural integration with DSPy's trace/trajectory patterns
4. **State Management**: Support both linear (conversation) and branching (RL/HTN) workflows

### Three-Layer API Design

#### Layer 1: Simple Linear API (Most Users)
```python
from claude_sdk import ClaudeAgent

agent = ClaudeAgent("/workspace")
response = agent.send("Build a TODO app")
response = agent.send("Add tests")  # Auto-continues

# Access results
print(response.text)
print(response.files_created)
print(response.cost)
```

#### Layer 2: DSPy Integration Layer
```python
from claude_sdk import Workspace, Conversation, Transition
import dspy

class ClaudeModule(dspy.Module):
    def __init__(self, workspace_path: str):
        self.workspace = Workspace(workspace_path)
        self.conversation = Conversation(self.workspace)
        
    def forward(self, prompt: str) -> Transition:
        """Execute and return full transition for DSPy to analyze"""
        return self.conversation.send(prompt)
    
    @property
    def trace(self) -> list[Transition]:
        """Expose conversation history as trace"""
        return self.conversation.history()
```

#### Layer 3: Low-Level Control (Power Users)
```python
from claude_sdk import Workspace, ClaudePrompt, EnvironmentSnapshot

workspace = Workspace("/project")

# Manual execution control
prompt = ClaudePrompt(
    text="Build app",
    continue_session=False,
    resume_session_id=None
)

before = workspace.snapshot()
execution = workspace.executor.execute(prompt)  
after = workspace.snapshot_with_session(execution.session_id)

# Build custom transition
transition = Transition(before, prompt, execution, after)
```

## Implementation Plan

### Phase 1: Rust Fixes (Required)

1. **Fix EnvironmentSnapshot Cloning**
```rust
// Add session_id for reconstruction
pub struct EnvironmentSnapshot {
    pub files: HashMap<PathBuf, String>,
    pub session_file: PathBuf,
    pub session_id: Option<String>,  // NEW
    pub timestamp: DateTime<Utc>,
    #[serde(skip)]
    pub session: Option<ParsedSession>,
}
```

2. **Integrate TransitionRecorder**
```rust
impl Conversation {
    pub fn new(workspace: Arc<Workspace>, record: bool) -> Self {
        Self {
            recorder: if record { 
                Some(TransitionRecorder::new(workspace.path())?) 
            } else { 
                None 
            },
            // ...
        }
    }
}
```

### Phase 2: PyO3 Bindings

1. **Core Types to Expose**
```rust
// src/python/execution.rs

#[pyclass]
pub struct PyWorkspace { inner: Arc<Workspace> }

#[pyclass]
pub struct PyConversation { inner: Conversation }

#[pyclass]
pub struct PyTransition { inner: Transition }

#[pyclass]
pub struct PyClaudePrompt { /* fields */ }

#[pyclass]
pub struct PyClaudeExecution { /* fields */ }

#[pyclass]
pub struct PyEnvironmentSnapshot { /* fields */ }
```

2. **Key Methods**
```rust
#[pymethods]
impl PyConversation {
    fn send(&mut self, prompt: &str) -> PyResult<PyTransition> {
        let transition = self.inner.send(prompt)?;
        Ok(PyTransition { inner: transition })
    }
    
    fn history(&self) -> Vec<PyTransition> {
        self.inner.history().iter()
            .map(|t| PyTransition { inner: t.clone() })
            .collect()
    }
}
```

### Phase 3: Python Wrapper Layer

1. **AgentResponse Wrapper**
```python
class AgentResponse:
    """User-friendly response wrapper"""
    def __init__(self, transition: Transition):
        self._transition = transition
        
    @property
    def text(self) -> str:
        return self._transition.execution.response
        
    @property
    def files_created(self) -> list[Path]:
        before = set(self._transition.before.files.keys())
        after = set(self._transition.after.files.keys())
        return list(after - before)
        
    @property
    def cost(self) -> float:
        return self._transition.execution.cost
```

2. **ClaudeAgent High-Level Interface**
```python
class ClaudeAgent:
    def __init__(self, workspace: str, auto_continue: bool = True):
        self.workspace = Workspace(workspace)
        self.conversation = Conversation(self.workspace)
        self.auto_continue = auto_continue
        
    def send(self, message: str, continue_: bool = None) -> AgentResponse:
        should_continue = continue_ if continue_ is not None else self.auto_continue
        
        if not should_continue:
            self.conversation = Conversation(self.workspace)
            
        transition = self.conversation.send(message)
        return AgentResponse(transition)
```

### Phase 4: DSPy Modules

1. **Basic Claude Module**
```python
class ClaudeModule(dspy.Module):
    """Basic DSPy integration - each forward() adds to trace"""
    def __init__(self, workspace_path: str):
        self.workspace = Workspace(workspace_path)
        self.conversation = Conversation(self.workspace)
        
    def forward(self, prompt: str) -> Transition:
        return self.conversation.send(prompt)
    
    @property
    def trace(self) -> list[Transition]:
        return self.conversation.history()
```

2. **ReAct-Style Module**
```python
class ClaudeReAct(dspy.Module):
    """ReAct pattern with trajectory tracking"""
    def __init__(self, workspace_path: str, max_iters: int = 5):
        self.workspace = Workspace(workspace_path)
        self.max_iters = max_iters
        
    def forward(self, task: str) -> dspy.Prediction:
        conversation = Conversation(self.workspace)
        trajectory = []
        
        for i in range(self.max_iters):
            prompt = self._build_prompt_with_trajectory(task, trajectory)
            transition = conversation.send(prompt)
            
            trajectory.append({
                'step': i,
                'reasoning': self._extract_reasoning(transition),
                'action': self._extract_action(transition),
                'observation': transition.execution.response,
                'transition': transition
            })
            
            if self._task_complete(transition):
                break
                
        return dspy.Prediction(
            answer=trajectory[-1]['observation'],
            trajectory=trajectory,
            transitions=conversation.history()
        )
```

3. **Branching Explorer Module**
```python
class ClaudeExplorer(dspy.Module):
    """For RL/optimization - explores multiple paths"""
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def forward(self, prompts: list[str]) -> list[Transition]:
        """Try multiple prompts from same starting state"""
        results = []
        
        for prompt in prompts:
            # Fresh workspace for each attempt
            workspace = Workspace(self.workspace_path)
            conv = Conversation(workspace)
            transition = conv.send(prompt)
            results.append(transition)
            
        return results
```

## Usage Examples

### Example 1: Simple Script Generation
```python
from claude_sdk import ClaudeAgent

agent = ClaudeAgent("./my_project")
agent.send("Create a Python script that fetches weather data")
agent.send("Add error handling")
agent.send("Add unit tests")

# Get all transitions for analysis
for t in agent.conversation.history():
    print(f"Step cost: ${t.execution.cost}")
    print(f"Tools used: {t.tools_used()}")
```

### Example 2: DSPy Optimization
```python
import dspy
from claude_sdk.dspy import ClaudeModule

# Configure DSPy
dspy.configure(lm=dspy.OpenAI(model="gpt-4"))

# Define task
class CodeGeneration(dspy.Signature):
    """Generate code to solve a problem"""
    problem = dspy.InputField()
    code = dspy.OutputField()

# Create optimizable module
claude = ClaudeModule("/workspace")

class CodeGenerator(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought(CodeGeneration)
        self.claude = claude
        
    def forward(self, problem):
        # Generate approach with DSPy
        approach = self.prog(problem=problem)
        
        # Execute with Claude
        transition = self.claude.forward(approach.code)
        
        return dspy.Prediction(
            code=transition.execution.response,
            files=transition.files_changed(),
            success=not transition.has_tool_errors()
        )

# Optimize on examples
optimizer = dspy.BootstrapFewShot(metric=lambda p: p.success)
optimized = optimizer.compile(CodeGenerator())
```

### Example 3: RL-Style Exploration
```python
from claude_sdk import ClaudeEnvironment

env = ClaudeEnvironment("/workspace")

# Checkpoint current state
state_0 = env.checkpoint()

# Try multiple approaches
results = []
for approach in ["Use React", "Use Vue", "Use vanilla JS"]:
    state, transition = env.explore_from(
        state=state_0,
        prompt=f"Build the UI {approach}"
    )
    
    reward = compute_reward(transition)
    results.append((approach, state, transition, reward))

# Continue from best
best = max(results, key=lambda x: x[3])
env.restore(best[1])
```

## Key Implementation Details

### Transition as Central Abstraction
Transitions capture everything needed for learning:
- **Before state**: Files and session before execution
- **Prompt**: What was asked
- **Execution**: What Claude did (response, cost, duration)
- **After state**: Files and session after execution

### Trace vs Trajectory
- **Trace** (our term): The `Vec<Transition>` in Conversation
- **Trajectory** (DSPy term): Reasoning steps with observations
- We provide both: raw transitions + formatted trajectory

### Session Management
- Each `conversation.send()` uses `--resume` with last session ID
- Creates sequential execution chain
- For branching: create new Conversation instances

### State Persistence
- Transitions can be saved via TransitionRecorder
- Conversations can be saved/loaded
- Enables learning from historical executions

## Testing Strategy

1. **Rust Unit Tests**: Verify core execution mechanics
2. **Python Integration Tests**: Test bindings and wrappers
3. **DSPy Example Tests**: Validate DSPy patterns work
4. **End-to-End Tests**: Full coding task completion

## Success Metrics

The API succeeds if:
1. Simple tasks require <5 lines of code
2. DSPy integration feels natural
3. Traces enable effective learning
4. Advanced patterns (RL/HTN) are possible
5. Performance overhead is minimal

## Future Extensions

1. **Async Support**: `await agent.send_async()`
2. **Streaming**: Real-time response streaming
3. **Multi-Workspace**: Parallel execution environments
4. **Tool Constraints**: Fine-grained tool permissions per execution
5. **Cost Optimization**: Budget-aware execution strategies