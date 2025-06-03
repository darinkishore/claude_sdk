use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use crate::execution::{ClaudePrompt, ClaudeExecution, EnvironmentSnapshot};

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