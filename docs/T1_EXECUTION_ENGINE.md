# T1: Execution Engine Specification

## Overview

T1 extends the Claude SDK with execution and orchestration capabilities, building on top of the existing T0 parser infrastructure. This document provides detailed implementation specifications for each component.

## Core Components

### 1. ClaudeExecutor

Wraps the Claude CLI to provide programmatic execution with structured responses.

#### Rust Implementation

```rust
// src/execution/executor.rs

use std::process::{Command, Output};
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudePrompt {
    pub text: String,
    pub continue_session: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudeExecution {
    pub prompt: ClaudePrompt,
    pub response: String,
    pub session_id: String,
    pub cost: f64,
    pub duration_ms: u64,
    pub tool_calls: Vec<String>,  // Tool names used
    pub model: String,
    pub timestamp: DateTime<Utc>,
}

pub struct ClaudeExecutor {
    claude_binary: PathBuf,
    working_directory: PathBuf,
}

impl ClaudeExecutor {
    pub fn new(working_directory: PathBuf) -> Result<Self, ExecutorError> {
        // Find claude binary
        let claude_binary = which::which("claude")
            .map_err(|_| ExecutorError::ClaudeNotFound)?;
        
        Ok(Self {
            claude_binary,
            working_directory,
        })
    }
    
    pub fn execute(&self, prompt: ClaudePrompt) -> Result<ClaudeExecution, ExecutorError> {
        let start = std::time::Instant::now();
        
        // Build command
        let mut cmd = Command::new(&self.claude_binary);
        cmd.current_dir(&self.working_directory)
           .arg("-p")  // Programmatic mode
           .arg("--output-format").arg("json");
           
        if prompt.continue_session {
            cmd.arg("--continue");
        }
        
        cmd.arg(&prompt.text);
        
        // Execute
        let output = cmd.output()
            .map_err(|e| ExecutorError::ExecutionFailed(e.to_string()))?;
            
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(ExecutorError::ClaudeFailed(stderr.to_string()));
        }
        
        // Parse JSON response
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: ClaudeJsonResponse = serde_json::from_str(&stdout)
            .map_err(|e| ExecutorError::ParseError(e.to_string()))?;
            
        Ok(ClaudeExecution {
            prompt,
            response: response.result,
            session_id: response.session_id,
            cost: response.cost_usd,
            duration_ms: start.elapsed().as_millis() as u64,
            tool_calls: extract_tool_calls(&response),
            model: response.model.unwrap_or_else(|| "unknown".to_string()),
            timestamp: Utc::now(),
        })
    }
}

// Expected JSON structure from claude --output-format json
#[derive(Deserialize)]
struct ClaudeJsonResponse {
    result: String,
    session_id: String,
    cost_usd: f64,
    #[serde(default)]
    model: Option<String>,
    // Additional fields we might use later
    #[serde(default)]
    total_cost: f64,
    #[serde(default)]
    duration_ms: u64,
}
```

#### Error Handling

```rust
#[derive(Debug, thiserror::Error)]
pub enum ExecutorError {
    #[error("Claude CLI not found in PATH")]
    ClaudeNotFound,
    
    #[error("Execution failed: {0}")]
    ExecutionFailed(String),
    
    #[error("Claude returned error: {0}")]
    ClaudeFailed(String),
    
    #[error("Failed to parse Claude response: {0}")]
    ParseError(String),
}
```

### 2. EnvironmentObserver

Captures snapshots of the environment state, reusing the existing T0 parser.

#### Rust Implementation

```rust
// src/execution/observer.rs

use std::path::{Path, PathBuf};
use std::collections::HashMap;
use glob::glob;
use crate::parser::SessionParser;
use crate::types::ParsedSession;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentSnapshot {
    pub files: HashMap<PathBuf, String>,
    pub session: ParsedSession,
    pub timestamp: DateTime<Utc>,
}

pub struct EnvironmentObserver {
    workspace: PathBuf,
    file_patterns: Vec<String>,
    session_parser: SessionParser,
}

impl EnvironmentObserver {
    pub fn new(workspace: PathBuf) -> Self {
        Self {
            workspace: workspace.clone(),
            file_patterns: vec![
                "**/*.py".to_string(),
                "**/*.rs".to_string(),
                "**/*.js".to_string(),
                "**/*.ts".to_string(),
                "**/*.jsx".to_string(),
                "**/*.tsx".to_string(),
                "**/*.json".to_string(),
                "**/*.toml".to_string(),
                "**/*.yaml".to_string(),
                "**/*.yml".to_string(),
                "**/*.md".to_string(),
                "**/Dockerfile".to_string(),
                "**/.gitignore".to_string(),
            ],
            session_parser: SessionParser::new(),
        }
    }
    
    pub fn snapshot(&self) -> Result<EnvironmentSnapshot, ObserverError> {
        let files = self.snapshot_files()?;
        let session = self.snapshot_session()?;
        
        Ok(EnvironmentSnapshot {
            files,
            session,
            timestamp: Utc::now(),
        })
    }
    
    fn snapshot_files(&self) -> Result<HashMap<PathBuf, String>, ObserverError> {
        let mut files = HashMap::new();
        
        for pattern in &self.file_patterns {
            let full_pattern = self.workspace.join(pattern);
            let pattern_str = full_pattern.to_string_lossy();
            
            for entry in glob(&pattern_str).map_err(|e| ObserverError::GlobError(e.to_string()))? {
                match entry {
                    Ok(path) => {
                        // Skip directories and non-readable files
                        if path.is_file() {
                            if let Ok(content) = std::fs::read_to_string(&path) {
                                // Store relative path
                                if let Ok(relative) = path.strip_prefix(&self.workspace) {
                                    files.insert(relative.to_path_buf(), content);
                                }
                            }
                        }
                    }
                    Err(_) => continue,
                }
            }
        }
        
        // Always include .claude directory JSONL files
        let claude_dir = self.workspace.join(".claude");
        if claude_dir.exists() {
            for entry in glob(&claude_dir.join("**/*.jsonl").to_string_lossy())
                .map_err(|e| ObserverError::GlobError(e.to_string()))? {
                if let Ok(path) = entry {
                    if let Ok(content) = std::fs::read_to_string(&path) {
                        if let Ok(relative) = path.strip_prefix(&self.workspace) {
                            files.insert(relative.to_path_buf(), content);
                        }
                    }
                }
            }
        }
        
        Ok(files)
    }
    
    fn snapshot_session(&self) -> Result<ParsedSession, ObserverError> {
        // Find the most recent session file
        let session_file = self.find_active_session_file()?;
        
        // Parse using existing T0 parser
        self.session_parser
            .parse_file(&session_file)
            .map_err(|e| ObserverError::ParseError(e.to_string()))
    }
    
    fn find_active_session_file(&self) -> Result<PathBuf, ObserverError> {
        let claude_projects = home::home_dir()
            .ok_or_else(|| ObserverError::HomeNotFound)?
            .join(".claude")
            .join("projects");
            
        // Find project directory matching our workspace
        let workspace_name = self.workspace
            .file_name()
            .ok_or_else(|| ObserverError::InvalidWorkspace)?
            .to_string_lossy();
            
        let project_dir = claude_projects.join(&*workspace_name);
        
        if !project_dir.exists() {
            return Err(ObserverError::ProjectNotFound(workspace_name.to_string()));
        }
        
        // Find most recent session file
        let mut session_files: Vec<_> = std::fs::read_dir(&project_dir)
            .map_err(|e| ObserverError::IoError(e.to_string()))?
            .filter_map(|entry| entry.ok())
            .filter(|entry| {
                entry.path().extension()
                    .map(|ext| ext == "jsonl")
                    .unwrap_or(false)
            })
            .collect();
            
        session_files.sort_by_key(|entry| {
            entry.metadata()
                .and_then(|m| m.modified())
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
        });
        
        session_files
            .last()
            .map(|entry| entry.path())
            .ok_or_else(|| ObserverError::NoSessionFound)
    }
}
```

### 3. TransitionRecorder

Stores transitions for learning and replay.

#### Storage Format

Transitions are stored as JSONL files in `.claude-sdk/transitions/` directory.

```rust
// src/execution/recorder.rs

use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transition {
    pub id: Uuid,
    pub before: EnvironmentSnapshot,
    pub prompt: ClaudePrompt,
    pub execution: ClaudeExecution,
    pub after: EnvironmentSnapshot,
    pub recorded_at: DateTime<Utc>,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

pub struct TransitionRecorder {
    storage_dir: PathBuf,
    current_session_file: PathBuf,
}

impl TransitionRecorder {
    pub fn new(workspace: &Path) -> Result<Self, RecorderError> {
        let storage_dir = workspace.join(".claude-sdk").join("transitions");
        create_dir_all(&storage_dir)
            .map_err(|e| RecorderError::StorageError(e.to_string()))?;
            
        let session_id = Uuid::new_v4();
        let current_session_file = storage_dir.join(format!("{}.jsonl", session_id));
        
        Ok(Self {
            storage_dir,
            current_session_file,
        })
    }
    
    pub fn record(&mut self, mut transition: Transition) -> Result<(), RecorderError> {
        transition.id = Uuid::new_v4();
        transition.recorded_at = Utc::now();
        
        let json = serde_json::to_string(&transition)
            .map_err(|e| RecorderError::SerializeError(e.to_string()))?;
            
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.current_session_file)
            .map_err(|e| RecorderError::StorageError(e.to_string()))?;
            
        writeln!(file, "{}", json)
            .map_err(|e| RecorderError::StorageError(e.to_string()))?;
            
        Ok(())
    }
    
    pub fn load(&self, id: Uuid) -> Result<Option<Transition>, RecorderError> {
        // Search through all transition files
        for entry in std::fs::read_dir(&self.storage_dir)
            .map_err(|e| RecorderError::StorageError(e.to_string()))? {
            
            let path = entry
                .map_err(|e| RecorderError::StorageError(e.to_string()))?
                .path();
                
            if path.extension().map(|e| e == "jsonl").unwrap_or(false) {
                let content = std::fs::read_to_string(&path)
                    .map_err(|e| RecorderError::StorageError(e.to_string()))?;
                    
                for line in content.lines() {
                    if let Ok(transition) = serde_json::from_str::<Transition>(line) {
                        if transition.id == id {
                            return Ok(Some(transition));
                        }
                    }
                }
            }
        }
        
        Ok(None)
    }
    
    pub fn recent(&self, limit: Option<usize>) -> Result<Vec<Transition>, RecorderError> {
        let mut transitions = Vec::new();
        
        // Read current session file
        if self.current_session_file.exists() {
            let content = std::fs::read_to_string(&self.current_session_file)
                .map_err(|e| RecorderError::StorageError(e.to_string()))?;
                
            for line in content.lines() {
                if let Ok(transition) = serde_json::from_str::<Transition>(line) {
                    transitions.push(transition);
                }
            }
        }
        
        // Apply limit if specified
        if let Some(limit) = limit {
            transitions.truncate(limit);
        }
        
        Ok(transitions)
    }
}
```

### 4. ClaudeEnvironment

Main orchestration interface that combines all components.

```rust
// src/execution/environment.rs

pub struct ClaudeEnvironment {
    executor: ClaudeExecutor,
    observer: EnvironmentObserver,
    recorder: TransitionRecorder,
    workspace: PathBuf,
}

impl ClaudeEnvironment {
    pub fn new(workspace: PathBuf) -> Result<Self, EnvironmentError> {
        let executor = ClaudeExecutor::new(workspace.clone())?;
        let observer = EnvironmentObserver::new(workspace.clone());
        let recorder = TransitionRecorder::new(&workspace)?;
        
        Ok(Self {
            executor,
            observer,
            recorder,
            workspace,
        })
    }
    
    pub fn execute(&mut self, prompt: &str) -> Result<Transition, EnvironmentError> {
        self.execute_with_options(prompt, true)
    }
    
    pub fn execute_with_options(
        &mut self, 
        prompt: &str, 
        continue_session: bool
    ) -> Result<Transition, EnvironmentError> {
        // Capture before state
        let before = self.observer.snapshot()?;
        
        // Execute prompt
        let claude_prompt = ClaudePrompt {
            text: prompt.to_string(),
            continue_session,
        };
        let execution = self.executor.execute(claude_prompt.clone())?;
        
        // Small delay to let file system settle
        std::thread::sleep(std::time::Duration::from_millis(500));
        
        // Capture after state
        let after = self.observer.snapshot()?;
        
        // Create transition
        let transition = Transition {
            id: Uuid::new_v4(),
            before,
            prompt: claude_prompt,
            execution,
            after,
            recorded_at: Utc::now(),
            metadata: serde_json::Value::Null,
        };
        
        // Record it
        self.recorder.record(transition.clone())?;
        
        Ok(transition)
    }
    
    pub fn history(&self, limit: Option<usize>) -> Result<Vec<Transition>, EnvironmentError> {
        self.recorder.recent(limit)
            .map_err(|e| EnvironmentError::RecorderError(e))
    }
    
    pub fn replay(&self, transition_id: Uuid) -> Result<Option<Transition>, EnvironmentError> {
        self.recorder.load(transition_id)
            .map_err(|e| EnvironmentError::RecorderError(e))
    }
}
```

## Python Bindings

### Enhanced Python API

```python
# python/claude_sdk/__init__.py additions

class ClaudeEnvironment:
    """Orchestration interface for Claude Code"""
    
    def __init__(self, workspace: Union[str, Path] = "."):
        self._env = _ClaudeEnvironment(str(Path(workspace).absolute()))
        
    def execute(self, prompt: str, continue_session: bool = True) -> Transition:
        """Execute a prompt and return the full transition"""
        return self._env.execute(prompt, continue_session)
        
    def history(self, limit: Optional[int] = None) -> List[Transition]:
        """Get recent transitions"""
        return self._env.history(limit)
        
    def replay(self, transition_id: str) -> Optional[Transition]:
        """Load a specific transition by ID"""
        return self._env.replay(transition_id)

class Transition:
    """A complete interaction cycle"""
    
    @property
    def files_created(self) -> List[Path]:
        """Files that were created in this transition"""
        before_files = set(self.before.files.keys())
        after_files = set(self.after.files.keys())
        return list(after_files - before_files)
        
    @property
    def files_modified(self) -> List[Path]:
        """Files that were modified in this transition"""
        modified = []
        for path in self.before.files:
            if path in self.after.files:
                if self.before.files[path] != self.after.files[path]:
                    modified.append(path)
        return modified
        
    @property
    def last_error(self) -> Optional[str]:
        """Extract last error from the transition"""
        # Implementation would search through messages
        pass
```

### Rust PyO3 Bindings

```rust
// src/python/environment.rs

#[pyclass(name = "ClaudeEnvironment")]
pub struct PyClaudeEnvironment {
    inner: ClaudeEnvironment,
}

#[pymethods]
impl PyClaudeEnvironment {
    #[new]
    fn new(workspace: String) -> PyResult<Self> {
        let env = ClaudeEnvironment::new(PathBuf::from(workspace))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to create environment: {}", e)
            ))?;
            
        Ok(Self { inner: env })
    }
    
    fn execute(&mut self, prompt: String, continue_session: bool) -> PyResult<PyTransition> {
        let transition = self.inner
            .execute_with_options(&prompt, continue_session)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Execution failed: {}", e)
            ))?;
            
        Ok(PyTransition::from_transition(transition))
    }
    
    fn history(&self, limit: Option<usize>) -> PyResult<Vec<PyTransition>> {
        let transitions = self.inner
            .history(limit)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to get history: {}", e)
            ))?;
            
        Ok(transitions.into_iter().map(PyTransition::from_transition).collect())
    }
}
```

## Testing Strategy

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_claude_executor_command_building() {
        // Test that commands are built correctly
        // Mock the actual execution
    }
    
    #[test]
    fn test_environment_observer_file_patterns() {
        // Test file inclusion/exclusion patterns
    }
    
    #[test]
    fn test_transition_recorder_persistence() {
        // Test saving and loading transitions
    }
}
```

### Integration Tests

```rust
// tests/integration/orchestration_test.rs

#[test]
#[ignore] // Run with --ignored flag when Claude is available
fn test_full_orchestration_cycle() {
    let temp_dir = tempdir().unwrap();
    let env = ClaudeEnvironment::new(temp_dir.path().to_path_buf()).unwrap();
    
    // Execute a simple prompt
    let transition = env.execute("Create a hello.py file with a hello world function").unwrap();
    
    // Verify file was created
    assert!(transition.after.files.contains_key(&PathBuf::from("hello.py")));
    
    // Verify we can load from history
    let history = env.history(Some(1)).unwrap();
    assert_eq!(history.len(), 1);
}
```

## Implementation Order

1. **ClaudeExecutor** - Start here, test with real Claude CLI
2. **EnvironmentObserver** - Reuse existing parser, add file snapshots  
3. **TransitionRecorder** - Simple JSONL storage
4. **ClaudeEnvironment** - Wire everything together
5. **Python bindings** - Expose clean API
6. **Integration tests** - Verify end-to-end flow

## Performance Considerations

- File snapshots should exclude large files (>1MB)
- Implement configurable file patterns
- Consider async execution for future versions
- Transition storage should handle large histories efficiently

## Error Recovery

All components should handle:
- Claude CLI not found
- Session files missing
- Workspace permissions issues
- Malformed JSONL
- Storage failures

Errors should be descriptive and actionable for users.