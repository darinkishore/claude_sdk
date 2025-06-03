# Architecture Patterns for Claude SDK Orchestration

This document presents three powerful patterns for orchestrating Claude Code, each suited to different use cases and complexity levels.

## Pattern 1: Reinforcement Learning (MDP) Architecture

### Overview

Model Claude Code orchestration as a Markov Decision Process where:
- **State**: Current environment (files, session, errors)
- **Action**: Prompt sent to Claude
- **Reward**: Success metrics (tests passing, goals met, cost efficiency)
- **Policy**: Learned mapping from states to optimal prompts

### When to Use

- You have clear success metrics
- You want to optimize over many iterations
- You're willing to invest in training
- You need cost or performance optimization

### Implementation

```python
import claude_sdk
from claude_sdk import ClaudeEnvironment, Transition
import dspy
from typing import List, Tuple

class ClaudeCodeMDP:
    """Claude Code as a Markov Decision Process"""
    
    def __init__(self, workspace: str):
        self.env = ClaudeEnvironment(workspace)
        self.policy = ClaudePolicy()  # DSPy module
        
    def reset(self) -> EnvironmentSnapshot:
        """Start fresh episode"""
        # Clear workspace or reset to initial state
        return self.env.observer.snapshot()
        
    def step(self, action: str) -> Tuple[EnvironmentSnapshot, float, bool]:
        """Execute action and return (next_state, reward, done)"""
        transition = self.env.execute(action)
        
        reward = self.compute_reward(transition)
        done = self.is_terminal(transition.after)
        
        return transition.after, reward, done
        
    def compute_reward(self, transition: Transition) -> float:
        """Define your reward function"""
        reward = 0.0
        
        # Positive rewards
        if self.tests_pass(transition.after):
            reward += 1.0
        if self.no_errors(transition.after):
            reward += 0.5
        if self.goal_progress(transition):
            reward += 0.3
            
        # Negative rewards
        reward -= transition.execution.cost * 0.1  # Cost penalty
        
        if self.introduced_error(transition):
            reward -= 1.0
            
        return reward
        
    def is_terminal(self, state: EnvironmentSnapshot) -> bool:
        """Check if we've reached a terminal state"""
        return (
            self.goal_achieved(state) or
            self.max_steps_reached() or
            self.budget_exceeded()
        )

@dspy.Module
class ClaudePolicy:
    """Learns optimal prompting policy π(a|s)"""
    
    def __init__(self):
        self.state_encoder = dspy.ChainOfThought(
            "state -> state_summary"
        )
        self.action_generator = dspy.Predict(
            "state_summary, goal -> action"
        )
        
    def forward(self, state: EnvironmentSnapshot, goal: str) -> str:
        # Encode state to natural language summary
        state_summary = self.state_encoder(
            state=self.state_to_text(state)
        ).state_summary
        
        # Generate optimal action
        action = self.action_generator(
            state_summary=state_summary,
            goal=goal
        ).action
        
        return action
        
    def state_to_text(self, state: EnvironmentSnapshot) -> str:
        """Convert state to text for DSPy"""
        return f"""
        Files: {list(state.files.keys())}
        Last message: {state.session.messages[-1].text if state.session.messages else 'None'}
        Errors: {self.extract_errors(state)}
        """

# Training Loop
def train_rl_agent(workspace: str, episodes: int = 100):
    mdp = ClaudeCodeMDP(workspace)
    policy = ClaudePolicy()
    optimizer = dspy.BootstrapFewShotWithRandomSearch(
        metric=lambda pred, trace: sum(r for _, r, _ in pred.trajectory)
    )
    
    training_data = []
    
    for episode in range(episodes):
        state = mdp.reset()
        trajectory = []
        total_reward = 0
        
        for step in range(50):  # Max steps per episode
            # Get action from policy
            action = policy(state, goal="Build a TODO app")
            
            # Execute in environment
            next_state, reward, done = mdp.step(action)
            
            # Record transition
            trajectory.append((state, action, reward))
            total_reward += reward
            
            state = next_state
            
            if done:
                break
                
        training_data.append({
            'trajectory': trajectory,
            'total_reward': total_reward
        })
        
        print(f"Episode {episode}: Total reward = {total_reward:.2f}")
    
    # Optimize policy based on best episodes
    best_episodes = sorted(training_data, key=lambda x: x['total_reward'], reverse=True)[:20]
    optimized_policy = optimizer.compile(policy, trainset=best_episodes)
    
    return optimized_policy

# Usage
if __name__ == "__main__":
    # Train an RL agent
    policy = train_rl_agent("./my_project", episodes=50)
    
    # Use trained policy
    mdp = ClaudeCodeMDP("./new_project")
    state = mdp.reset()
    
    while True:
        action = policy(state, "Build a REST API")
        state, reward, done = mdp.step(action)
        
        if done:
            print("Goal achieved!")
            break
```

### Advanced Features

```python
class AdvancedClaudeMDP(ClaudeCodeMDP):
    """Enhanced MDP with advanced features"""
    
    def __init__(self, workspace: str):
        super().__init__(workspace)
        self.experience_replay = []
        self.q_values = {}  # State-action values
        
    def add_experience_replay(self, transition: Transition, reward: float):
        """Store experiences for offline learning"""
        self.experience_replay.append({
            'transition': transition,
            'reward': reward,
            'state_hash': self.hash_state(transition.before),
            'action': transition.prompt.text
        })
        
    def get_q_value(self, state_hash: str, action: str) -> float:
        """Get estimated value of state-action pair"""
        return self.q_values.get((state_hash, action), 0.0)
        
    def update_q_value(self, state_hash: str, action: str, value: float):
        """Update Q-value estimates"""
        self.q_values[(state_hash, action)] = value
        
    def epsilon_greedy_action(self, state: EnvironmentSnapshot, epsilon: float = 0.1) -> str:
        """Exploration vs exploitation"""
        import random
        
        if random.random() < epsilon:
            # Explore: random action
            return self.random_action_generator(state)
        else:
            # Exploit: best known action
            return self.policy(state, self.goal)
```

## Pattern 2: Hierarchical Task Network (HTN) Architecture

### Overview

Decompose complex goals into hierarchical subtasks that Claude can execute atomically. Each high-level task breaks down into subtasks until reaching executable Claude prompts.

### When to Use

- You have complex, multi-step projects
- Tasks have natural hierarchical structure
- You want explainable decomposition
- You need checkpointing and resumption

### Implementation

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class TaskNode:
    """Node in the task hierarchy"""
    id: str
    goal: str
    parent: Optional['TaskNode']
    children: List['TaskNode']
    status: TaskStatus
    context: dict
    attempts: List[Tuple[str, Transition]]  # (prompt, transition) pairs
    
    def __init__(self, goal: str, parent: Optional['TaskNode'] = None):
        self.id = str(uuid.uuid4())
        self.goal = goal
        self.parent = parent
        self.children = []
        self.status = TaskStatus.PENDING
        self.context = {}
        self.attempts = []
        
    def add_child(self, child: 'TaskNode'):
        self.children.append(child)
        child.parent = self
        
    def is_leaf(self) -> bool:
        return len(self.children) == 0
        
    def is_complete(self) -> bool:
        if self.is_leaf():
            return self.status == TaskStatus.COMPLETED
        return all(child.is_complete() for child in self.children)

class ClaudeHTNPlanner:
    """Hierarchical Task Network planner for Claude Code"""
    
    def __init__(self, env: ClaudeEnvironment):
        self.env = env
        self.task_decomposer = TaskDecomposer()
        self.task_executor = TaskExecutor()
        self.task_tree = None
        
    def plan_and_execute(self, root_goal: str) -> TaskNode:
        """Main planning and execution loop"""
        self.task_tree = TaskNode(root_goal)
        
        # Decompose the root goal
        self._decompose_recursive(self.task_tree)
        
        # Execute leaf tasks in order
        self._execute_tree(self.task_tree)
        
        return self.task_tree
        
    def _decompose_recursive(self, task: TaskNode, depth: int = 0):
        """Recursively decompose tasks"""
        if depth > 5:  # Max decomposition depth
            return
            
        # Check if task is atomic (can be executed directly)
        if self.task_decomposer.is_atomic(task.goal, task.context):
            return
            
        # Decompose into subtasks
        subtasks = self.task_decomposer.decompose(task.goal, task.context)
        
        for subtask_goal in subtasks:
            child = TaskNode(subtask_goal, parent=task)
            child.context = self._inherit_context(task.context)
            task.add_child(child)
            
            # Recursively decompose child
            self._decompose_recursive(child, depth + 1)
            
    def _execute_tree(self, task: TaskNode):
        """Execute task tree in depth-first order"""
        if task.is_leaf():
            # Execute atomic task
            self._execute_leaf_task(task)
        else:
            # Execute children first
            for child in task.children:
                self._execute_tree(child)
                
            # Check if parent task is now complete
            if task.is_complete():
                task.status = TaskStatus.COMPLETED
                
    def _execute_leaf_task(self, task: TaskNode):
        """Execute a single atomic task"""
        task.status = TaskStatus.IN_PROGRESS
        
        # Generate prompt for this task
        prompt = self.task_executor.generate_prompt(
            task.goal,
            task.context,
            task.parent.goal if task.parent else None,
            [attempt[0] for attempt in task.attempts]  # Previous prompts
        )
        
        # Execute with Claude
        try:
            transition = self.env.execute(prompt)
            task.attempts.append((prompt, transition))
            
            # Check if task succeeded
            if self.task_executor.verify_success(task.goal, transition):
                task.status = TaskStatus.COMPLETED
                self._update_parent_context(task, transition)
            else:
                # Retry with refined prompt
                if len(task.attempts) < 3:
                    self._execute_leaf_task(task)
                else:
                    task.status = TaskStatus.FAILED
                    
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.context['error'] = str(e)

@dspy.Module
class TaskDecomposer:
    """Learns to decompose tasks into subtasks"""
    
    def __init__(self):
        self.decomposition = dspy.ChainOfThought(
            "task, context -> subtasks"
        )
        self.atomicity_check = dspy.Predict(
            "task -> is_atomic"
        )
        
    def is_atomic(self, task: str, context: dict) -> bool:
        """Check if task can be executed directly"""
        result = self.atomicity_check(task=task)
        return result.is_atomic.lower() == "yes"
        
    def decompose(self, task: str, context: dict) -> List[str]:
        """Break down task into subtasks"""
        result = self.decomposition(
            task=task,
            context=str(context)
        )
        
        # Parse subtasks from response
        subtasks = self._parse_subtasks(result.subtasks)
        return subtasks
        
    def _parse_subtasks(self, text: str) -> List[str]:
        """Extract subtask list from text"""
        # Simple parsing - could be enhanced
        lines = text.strip().split('\n')
        subtasks = []
        for line in lines:
            if line.strip().startswith(('- ', '* ', '1.', '2.', '3.')):
                subtasks.append(line.strip().lstrip('- *123456789.').strip())
        return subtasks

@dspy.Module 
class TaskExecutor:
    """Converts leaf tasks to Claude prompts"""
    
    def __init__(self):
        self.prompt_generator = dspy.ChainOfThought(
            "task, context, parent_task, previous_attempts -> prompt"
        )
        self.success_verifier = dspy.Predict(
            "task, execution_result -> success"
        )
        
    def generate_prompt(self, task: str, context: dict, 
                       parent_task: Optional[str], 
                       previous_attempts: List[str]) -> str:
        """Generate optimal prompt for task"""
        result = self.prompt_generator(
            task=task,
            context=str(context),
            parent_task=parent_task or "None",
            previous_attempts=str(previous_attempts)
        )
        return result.prompt
        
    def verify_success(self, task: str, transition: Transition) -> bool:
        """Check if task was completed successfully"""
        result = self.success_verifier(
            task=task,
            execution_result=transition.execution.response
        )
        return result.success.lower() == "yes"

# Example Usage
def build_web_app_with_htn():
    """Example: Build a web app using HTN planning"""
    env = ClaudeEnvironment("./web_app")
    planner = ClaudeHTNPlanner(env)
    
    # High-level goal
    task_tree = planner.plan_and_execute(
        "Build a full-stack web application with user authentication"
    )
    
    # The planner might decompose this into:
    # 1. Set up project structure
    #    1.1 Create backend directory
    #    1.2 Create frontend directory
    #    1.3 Initialize package.json files
    # 2. Implement backend
    #    2.1 Set up Express server
    #    2.2 Create user model
    #    2.3 Implement auth routes
    # 3. Implement frontend
    #    3.1 Create React app
    #    3.2 Build login form
    #    3.3 Add route protection
    # etc...
    
    # Visualize the task tree
    print_task_tree(task_tree)
    
    # Get execution summary
    print(f"Total tasks: {count_tasks(task_tree)}")
    print(f"Completed: {count_completed_tasks(task_tree)}")
    print(f"Failed: {count_failed_tasks(task_tree)}")
    
def print_task_tree(task: TaskNode, depth: int = 0):
    """Pretty print the task hierarchy"""
    indent = "  " * depth
    status_icon = {
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.PENDING: "⏳",
        TaskStatus.BLOCKED: "🚫"
    }[task.status]
    
    print(f"{indent}{status_icon} {task.goal}")
    
    for child in task.children:
        print_task_tree(child, depth + 1)
```

### Advanced HTN Features

```python
class AdvancedHTNPlanner(ClaudeHTNPlanner):
    """Enhanced HTN with advanced capabilities"""
    
    def __init__(self, env: ClaudeEnvironment):
        super().__init__(env)
        self.checkpoint_manager = CheckpointManager()
        self.dependency_resolver = DependencyResolver()
        
    def plan_with_dependencies(self, root_goal: str) -> TaskNode:
        """Plan with task dependencies"""
        task_tree = TaskNode(root_goal)
        
        # Decompose tasks
        self._decompose_recursive(task_tree)
        
        # Analyze dependencies
        self.dependency_resolver.analyze(task_tree)
        
        # Execute respecting dependencies
        self._execute_with_dependencies(task_tree)
        
        return task_tree
        
    def resume_from_checkpoint(self, checkpoint_id: str) -> TaskNode:
        """Resume execution from saved checkpoint"""
        task_tree = self.checkpoint_manager.load(checkpoint_id)
        
        # Find incomplete tasks
        incomplete_tasks = self._find_incomplete_tasks(task_tree)
        
        # Resume execution
        for task in incomplete_tasks:
            if task.status != TaskStatus.BLOCKED:
                self._execute_tree(task)
                
        return task_tree
        
    def _execute_with_dependencies(self, task: TaskNode):
        """Execute tasks respecting dependency order"""
        # Get execution order
        execution_order = self.dependency_resolver.get_execution_order(task)
        
        for task_node in execution_order:
            if task_node.is_leaf() and task_node.status == TaskStatus.PENDING:
                # Check if dependencies are satisfied
                if self.dependency_resolver.dependencies_satisfied(task_node):
                    self._execute_leaf_task(task_node)
                else:
                    task_node.status = TaskStatus.BLOCKED
                    
    def save_checkpoint(self, name: str):
        """Save current execution state"""
        if self.task_tree:
            self.checkpoint_manager.save(self.task_tree, name)
```

## Pattern 3: Stream Processing (Reactive) Architecture

### Overview

Model Claude orchestration as streams of events where:
- File changes trigger re-evaluation
- Test results flow into decision making
- Claude outputs feed back into the system
- Everything is reactive and composable

### When to Use

- You need real-time responsiveness
- You have multiple event sources
- You want composable operators
- You prefer functional reactive programming

### Implementation

```python
from rx import Observable, Subject, operators as ops
from rx.scheduler import ThreadPoolScheduler
import asyncio
from typing import Dict, Any

class ClaudeReactiveOrchestrator:
    """Reactive orchestration using observables"""
    
    def __init__(self, env: ClaudeEnvironment):
        self.env = env
        
        # Event streams
        self.file_changes = Subject()
        self.test_results = Subject()
        self.claude_responses = Subject()
        self.user_goals = Subject()
        self.errors = Subject()
        
        # Schedulers
        self.thread_pool = ThreadPoolScheduler()
        
        # Setup reactive pipeline
        self._setup_pipeline()
        
    def _setup_pipeline(self):
        """Configure the reactive data flow"""
        
        # Combine relevant streams into context
        context_stream = Observable.combine_latest(
            self.file_changes.pipe(
                ops.buffer_with_time(1000),  # Buffer file changes
                ops.map(lambda files: {'changed_files': files})
            ),
            self.test_results.pipe(
                ops.start_with({'status': 'unknown'}),
                ops.map(lambda result: {'test_status': result})
            ),
            self.claude_responses.pipe(
                ops.start_with(None),
                ops.map(lambda resp: {'last_response': resp})
            ),
            self.user_goals.pipe(
                ops.distinct_until_changed(),
                ops.map(lambda goal: {'current_goal': goal})
            )
        ).pipe(
            ops.map(lambda contexts: {k: v for d in contexts for k, v in d.items()})
        )
        
        # Generate prompts from context
        prompt_stream = context_stream.pipe(
            ops.debounce(2.0),  # Don't overwhelm Claude
            ops.map(self._generate_prompt),
            ops.filter(lambda prompt: prompt is not None)
        )
        
        # Execute prompts
        execution_stream = prompt_stream.pipe(
            ops.flat_map(self._execute_prompt_async),
            ops.retry(3),
            ops.catch(self._handle_error)
        )
        
        # Subscribe to execution results
        execution_stream.subscribe(
            on_next=self._process_result,
            on_error=lambda e: self.errors.on_next(e)
        )
        
    def _generate_prompt(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate prompt based on current context"""
        if not context.get('current_goal'):
            return None
            
        # Use DSPy or rules to generate prompt
        prompt_generator = ReactivePromptGenerator()
        return prompt_generator.generate(context)
        
    def _execute_prompt_async(self, prompt: str) -> Observable:
        """Execute prompt asynchronously"""
        def execute():
            transition = self.env.execute(prompt)
            return transition
            
        return Observable.start(execute, scheduler=self.thread_pool)
        
    def _process_result(self, transition: Transition):
        """Process execution results"""
        # Emit response
        self.claude_responses.on_next(transition.execution.response)
        
        # Check for test changes
        self._check_tests(transition)
        
        # Check for file changes
        self._detect_file_changes(transition)
        
    def _handle_error(self, error: Exception, source: Observable) -> Observable:
        """Error recovery strategy"""
        self.errors.on_next(error)
        
        # Retry with modified prompt
        recovery_prompt = f"The previous attempt failed with: {error}. Please try a different approach."
        return Observable.just(recovery_prompt).pipe(
            ops.delay(5.0),
            ops.flat_map(self._execute_prompt_async)
        )
        
    def start_watching(self, workspace: str):
        """Start file system watcher"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class Handler(FileSystemEventHandler):
            def __init__(self, file_subject):
                self.file_subject = file_subject
                
            def on_modified(self, event):
                if not event.is_directory:
                    self.file_subject.on_next(event.src_path)
                    
        handler = Handler(self.file_changes)
        observer = Observer()
        observer.schedule(handler, workspace, recursive=True)
        observer.start()
        
    def run_goal(self, goal: str):
        """Execute a goal reactively"""
        # Set the goal
        self.user_goals.on_next(goal)
        
        # The reactive pipeline will handle the rest
        
@dspy.Module
class ReactivePromptGenerator:
    """Generates prompts reactively based on context"""
    
    def __init__(self):
        self.context_analyzer = dspy.ChainOfThought(
            "context -> situation_analysis"
        )
        self.prompt_creator = dspy.Predict(
            "situation, goal -> prompt"
        )
        
    def generate(self, context: Dict[str, Any]) -> str:
        # Analyze current situation
        situation = self.context_analyzer(
            context=str(context)
        ).situation_analysis
        
        # Generate appropriate prompt
        prompt = self.prompt_creator(
            situation=situation,
            goal=context['current_goal']
        ).prompt
        
        return prompt

# Advanced Reactive Patterns
class AdvancedReactiveOrchestrator(ClaudeReactiveOrchestrator):
    """Enhanced reactive patterns"""
    
    def __init__(self, env: ClaudeEnvironment):
        super().__init__(env)
        
        # Additional streams
        self.performance_metrics = Subject()
        self.cost_tracker = Subject()
        
    def setup_performance_monitoring(self):
        """Monitor and optimize performance"""
        
        # Track execution times
        self.claude_responses.pipe(
            ops.pairwise(),
            ops.map(lambda pair: pair[1].timestamp - pair[0].timestamp),
            ops.scan(lambda acc, x: {
                'avg_time': (acc['avg_time'] * acc['count'] + x) / (acc['count'] + 1),
                'count': acc['count'] + 1
            }, {'avg_time': 0, 'count': 0})
        ).subscribe(self.performance_metrics)
        
        # Cost optimization
        self.claude_responses.pipe(
            ops.map(lambda t: t.execution.cost),
            ops.scan(lambda acc, cost: acc + cost, 0),
            ops.filter(lambda total: total > 10.0)  # Alert on high cost
        ).subscribe(
            lambda cost: print(f"⚠️ High cost alert: ${cost:.2f}")
        )
        
    def create_test_driven_pipeline(self):
        """Test-driven development pipeline"""
        
        # Run tests after each Claude execution
        test_pipeline = self.claude_responses.pipe(
            ops.delay(2.0),  # Let file system settle
            ops.flat_map(lambda _: Observable.start(self._run_tests)),
            ops.share()  # Share results
        )
        
        # Feed test results back
        test_pipeline.subscribe(self.test_results)
        
        # Auto-fix failing tests
        test_pipeline.pipe(
            ops.filter(lambda result: not result['passing']),
            ops.throttle_first(5.0),  # Don't spam fixes
            ops.map(lambda result: f"Fix the failing test: {result['error']}")
        ).subscribe(
            lambda prompt: self.env.execute(prompt)
        )

# Example Usage
def reactive_development():
    """Example of reactive Claude orchestration"""
    env = ClaudeEnvironment("./my_project")
    orchestrator = AdvancedReactiveOrchestrator(env)
    
    # Setup monitoring
    orchestrator.setup_performance_monitoring()
    orchestrator.create_test_driven_pipeline()
    
    # Start file watching
    orchestrator.start_watching("./my_project")
    
    # Subscribe to errors for debugging
    orchestrator.errors.subscribe(
        lambda e: print(f"Error: {e}")
    )
    
    # Set goal and let the system react
    orchestrator.run_goal("Build a REST API with automatic test fixing")
    
    # Keep running
    try:
        input("Press Enter to stop...")
    except KeyboardInterrupt:
        pass
```

## Pattern Comparison

| Aspect | RL/MDP | HTN | Reactive |
|--------|---------|-----|----------|
| **Complexity** | Medium | High | Medium |
| **Learning** | Built-in | Can be added | Can be added |
| **Explainability** | Low | High | Medium |
| **Real-time** | No | No | Yes |
| **Checkpointing** | Manual | Built-in | Stream-based |
| **Best for** | Optimization | Complex projects | Interactive development |

## Combining Patterns

These patterns can be combined for even more powerful orchestration:

```python
class HybridOrchestrator:
    """Combines HTN planning with RL optimization"""
    
    def __init__(self, env: ClaudeEnvironment):
        self.env = env
        self.htn_planner = ClaudeHTNPlanner(env)
        self.rl_optimizer = ClaudeCodeMDP(env.workspace)
        
    def plan_and_optimize(self, goal: str):
        # Use HTN to decompose
        task_tree = self.htn_planner._decompose_recursive(TaskNode(goal))
        
        # Use RL to optimize execution of each leaf task
        for task in self._get_leaf_tasks(task_tree):
            # Learn optimal prompt for this task type
            optimal_prompt = self.rl_optimizer.policy(
                self.env.observer.snapshot(),
                task.goal
            )
            
            # Execute with optimal prompt
            transition = self.env.execute(optimal_prompt)
            
            # Update RL model with result
            reward = self._evaluate_execution(transition, task)
            self.rl_optimizer.update_policy(transition, reward)
```

## Conclusion

Each pattern offers unique advantages:

1. **RL/MDP**: Best for learning and optimization over many iterations
2. **HTN**: Best for complex, hierarchical projects with clear structure  
3. **Reactive**: Best for real-time, event-driven development

Choose based on your specific needs, or combine patterns for maximum flexibility. The Claude SDK provides the primitives; these patterns show how to orchestrate them effectively.