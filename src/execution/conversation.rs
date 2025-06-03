//! Conversation abstraction that owns its transition history
//!
//! This is the new Conversation-centric design where each conversation
//! maintains its own history of transitions.

use std::sync::Arc;
use std::path::PathBuf;
use uuid::Uuid;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};

use super::{
    Workspace, WorkspaceError,
    ClaudePrompt,
    EnvironmentSnapshot, Transition,
};

/// A conversation with Claude that maintains its own history
pub struct Conversation {
    /// Unique ID for this conversation
    id: Uuid,
    
    /// The workspace where this conversation executes
    workspace: Arc<Workspace>,
    
    /// All transitions in this conversation
    transitions: Vec<Transition>,
    
    /// Chain of session IDs (Claude creates new ID per execution)
    session_ids: Vec<String>,
    
    /// Metadata about the conversation
    metadata: ConversationMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationMetadata {
    pub created_at: DateTime<Utc>,
    pub workspace_path: PathBuf,
    pub total_cost_usd: f64,
    pub total_messages: usize,
}

impl Conversation {
    /// Create a new conversation in the given workspace
    pub fn new(workspace: Arc<Workspace>) -> Self {
        Self {
            id: Uuid::new_v4(),
            workspace: workspace.clone(),
            transitions: Vec::new(),
            session_ids: Vec::new(),
            metadata: ConversationMetadata {
                created_at: Utc::now(),
                workspace_path: workspace.path().clone(),
                total_cost_usd: 0.0,
                total_messages: 0,
            },
        }
    }
    
    /// Send a message in this conversation
    pub fn send(&mut self, message: &str) -> Result<Transition, ConversationError> {
        // Capture before state
        let before = if self.session_ids.is_empty() {
            // First message - no session to snapshot
            EnvironmentSnapshot {
                files: self.workspace.snapshot()?.files,
                session_file: PathBuf::new(),
                timestamp: Utc::now(),
                session: None,
            }
        } else {
            // Continuing - snapshot current state
            self.workspace.snapshot()?
        };
        
        // Build prompt with resume_session_id if continuing
        let prompt = ClaudePrompt {
            text: message.to_string(),
            continue_session: false,  // Never use the ambiguous continue flag
            resume_session_id: self.session_ids.last().cloned(),
        };
        
        // Execute via workspace
        let execution = self.workspace.executor.execute(prompt.clone())?;
        
        // Small delay to let filesystem settle
        std::thread::sleep(std::time::Duration::from_millis(500));
        
        // Capture after state with new session ID
        let after = self.workspace.snapshot_with_session(&execution.session_id)?;
        
        // Create transition
        let transition = Transition {
            id: Uuid::new_v4(),
            before,
            prompt,
            execution: execution.clone(),
            after,
            recorded_at: Utc::now(),
            metadata: serde_json::json!({
                "conversation_id": self.id.to_string(),
            }),
        };
        
        // Update conversation state
        self.session_ids.push(execution.session_id);
        self.metadata.total_cost_usd += execution.cost;
        self.metadata.total_messages += 1;
        
        // Store and return the transition
        self.transitions.push(transition.clone());
        Ok(transition)
    }
    
    /// Get all transitions in this conversation
    pub fn history(&self) -> &[Transition] {
        &self.transitions
    }
    
    /// Get the conversation ID
    pub fn id(&self) -> Uuid {
        self.id
    }
    
    /// Get conversation metadata
    pub fn metadata(&self) -> &ConversationMetadata {
        &self.metadata
    }
    
    /// Get all session IDs in order
    pub fn session_ids(&self) -> &[String] {
        &self.session_ids
    }
    
    /// Get the most recent transition
    pub fn last_transition(&self) -> Option<&Transition> {
        self.transitions.last()
    }
    
    /// Get total cost of the conversation
    pub fn total_cost(&self) -> f64 {
        self.metadata.total_cost_usd
    }
    
    /// Get tools used across all transitions
    pub fn tools_used(&self) -> Vec<String> {
        let mut tools = std::collections::HashSet::new();
        for transition in &self.transitions {
            for tool in &transition.execution.tool_calls {
                tools.insert(tool.clone());
            }
        }
        let mut result: Vec<String> = tools.into_iter().collect();
        result.sort();
        result
    }
    
    /// Save conversation to disk
    pub fn save(&self, path: &std::path::Path) -> Result<(), ConversationError> {
        let data = serde_json::to_string_pretty(self)?;
        std::fs::write(path, data)?;
        Ok(())
    }
    
    /// Load conversation from disk
    pub fn load(path: &std::path::Path, workspace: Arc<Workspace>) -> Result<Self, ConversationError> {
        let data = std::fs::read_to_string(path)?;
        let mut conv: Self = serde_json::from_str(&data)?;
        conv.workspace = workspace;  // Update workspace reference
        Ok(conv)
    }
}

// Make Conversation serializable (excludes workspace Arc)
impl Serialize for Conversation {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("Conversation", 5)?;
        state.serialize_field("id", &self.id)?;
        state.serialize_field("transitions", &self.transitions)?;
        state.serialize_field("session_ids", &self.session_ids)?;
        state.serialize_field("metadata", &self.metadata)?;
        state.end()
    }
}

impl<'de> Deserialize<'de> for Conversation {
    fn deserialize<D>(_deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        // Placeholder - need workspace to properly deserialize
        Err(serde::de::Error::custom("Use Conversation::load() instead"))
    }
}

#[derive(Debug, thiserror::Error)]
pub enum ConversationError {
    #[error("Workspace error: {0}")]
    WorkspaceError(#[from] WorkspaceError),
    
    #[error("Executor error: {0}")]
    ExecutorError(#[from] super::ExecutorError),
    
    #[error("Observer error: {0}")]  
    ObserverError(#[from] super::ObserverError),
    
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}