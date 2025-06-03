use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use crate::execution::{ClaudePrompt, ClaudeExecution, EnvironmentSnapshot};
use crate::types::{MessageRecord, ContentBlock, ToolExecution, ToolResult as TypesToolResult};
use std::time::Duration;

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

impl Transition {
    /// Get the new messages added in this transition
    pub fn new_messages(&self) -> Vec<&MessageRecord> {
        match (&self.before.session, &self.after.session) {
            (Some(before_session), Some(after_session)) => {
                let before_count = before_session.messages.len();
                after_session.messages.iter()
                    .skip(before_count)
                    .collect()
            }
            (None, Some(after_session)) => {
                // First execution, all messages are new
                after_session.messages.iter().collect()
            }
            _ => Vec::new(),
        }
    }
    
    /// Extract tool executions from this transition
    pub fn tool_executions(&self) -> Vec<ToolExecution> {
        let mut executions = Vec::new();
        let new_messages = self.new_messages();
        
        // Track tool uses waiting for results
        let mut pending_tools: std::collections::HashMap<String, (String, serde_json::Value, DateTime<Utc>)> = 
            std::collections::HashMap::new();
        
        for message in new_messages {
            for content in &message.message.content {
                match content {
                    ContentBlock::ToolUse { id, name, input } => {
                        // Record tool use
                        pending_tools.insert(
                            id.clone(), 
                            (name.clone(), input.clone(), message.timestamp)
                        );
                    }
                    ContentBlock::ToolResult { tool_use_id, content, is_error } => {
                        // Match with tool use
                        if let Some((tool_name, input, start_time)) = pending_tools.remove(tool_use_id) {
                            let duration = message.timestamp.signed_duration_since(start_time)
                                .to_std()
                                .unwrap_or(Duration::from_secs(0));
                            
                            let tool_result = TypesToolResult {
                                tool_use_id: tool_use_id.clone(),
                                content: content.as_ref()
                                    .map(|c| c.as_text())
                                    .unwrap_or_default(),
                                stdout: None,  // Could parse from content
                                stderr: None,
                                interrupted: false,
                                is_error: is_error.unwrap_or(false),
                                metadata: serde_json::Value::Null,
                            };
                            
                            executions.push(ToolExecution::new(
                                tool_name,
                                input,
                                tool_result,
                                duration,
                                start_time,
                            ));
                        }
                    }
                    _ => {}
                }
            }
        }
        
        executions
    }
    
    /// Get just the tool names used in this transition
    pub fn tools_used(&self) -> Vec<String> {
        self.tool_executions()
            .into_iter()
            .map(|exec| exec.tool_name)
            .collect()
    }
    
    /// Check if any tools failed in this transition
    pub fn has_tool_errors(&self) -> bool {
        self.tool_executions()
            .iter()
            .any(|exec| !exec.is_success())
    }
}

pub struct TransitionRecorder {
    storage_dir: PathBuf,
    current_session_file: PathBuf,
}

impl TransitionRecorder {
    pub fn new(workspace: &Path) -> Result<Self, RecorderError> {
        // Use workspace-scoped storage for transitions
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
        // Only set ID if not already set
        if transition.id == Uuid::nil() {
            transition.id = Uuid::new_v4();
        }
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
        
        // Read all session log files
        for entry in std::fs::read_dir(&self.storage_dir)
            .map_err(|e| RecorderError::StorageError(e.to_string()))?
        {
            let path = match entry {
                Ok(e) => e.path(),
                Err(e) => return Err(RecorderError::StorageError(e.to_string())),
            };

            if path.extension().map(|e| e == "jsonl").unwrap_or(false) {
                let content = std::fs::read_to_string(&path)
                    .map_err(|e| RecorderError::StorageError(e.to_string()))?;

                for line in content.lines() {
                    if let Ok(transition) = serde_json::from_str::<Transition>(line) {
                        transitions.push(transition);
                    }
                }
            }
        }
        
        // Sort by timestamp (newest first)
        transitions.sort_by(|a, b| b.recorded_at.cmp(&a.recorded_at));
        
        // Apply limit if specified
        if let Some(limit) = limit {
            transitions.truncate(limit);
        }
        
        Ok(transitions)
    }
}

#[derive(Debug, thiserror::Error)]
pub enum RecorderError {
    #[error("Storage error: {0}")]
    StorageError(String),
    
    #[error("Serialization error: {0}")]
    SerializeError(String),
}