//! Conversation abstraction that owns its transition history
//!
//! This is the new Conversation-centric design where each conversation
//! maintains its own history of transitions.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use uuid::Uuid;

use super::{
    Workspace, WorkspaceError,
    ClaudePrompt,
    EnvironmentSnapshot, Transition,
    recorder::{TransitionRecorder, RecorderError},
    observer::{PRE_CONVERSATION_SESSION_ID, NO_SESSION_FILE},
};

/// Serializable representation of a Conversation
#[derive(Debug, Serialize, Deserialize)]
struct SavedConversation {
    id: Uuid,
    transitions: Vec<Transition>,
    session_ids: Vec<String>,
    metadata: ConversationMetadata,
    #[serde(default)]
    recording_enabled: bool,
}

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

    /// Optional recorder for persisting transitions to disk
    recorder: Option<TransitionRecorder>,
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
        Self::new_with_options(workspace, false).expect("record=false cannot fail")
    }

    /// Create a new conversation with options
    pub fn new_with_options(
        workspace: Arc<Workspace>,
        record: bool,
    ) -> Result<Self, ConversationError> {
        let recorder = if record {
            Some(TransitionRecorder::new(workspace.path())?)
        } else {
            None
        };

        Ok(Self {
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
            recorder,
        })
    }

    /// Send a message in this conversation
    pub fn send(&mut self, message: &str) -> Result<Transition, ConversationError> {
        // Capture before state
        let before = if self.session_ids.is_empty() {
            // First message - no session to snapshot
            EnvironmentSnapshot {
                files: self.workspace.snapshot_files()?,
                session_file: PathBuf::from(NO_SESSION_FILE),
                session_id: Some(PRE_CONVERSATION_SESSION_ID.to_string()),
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
            continue_session: false, // Never use the ambiguous continue flag
            resume_session_id: self.session_ids.last().cloned(),
        };

        // Execute via workspace
        let execution = self.workspace.executor.execute(prompt.clone())?;

        // Small delay to let file system settle
        std::thread::sleep(std::time::Duration::from_millis(500));

        // Capture after state with new session ID
        let after = self
            .workspace
            .snapshot_with_session(&execution.session_id)?;

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

        // Record if recorder is enabled
        if let Some(ref mut recorder) = self.recorder {
            if let Err(e) = recorder.record(&transition) {
                eprintln!("Warning: Failed to record transition: {}", e);
            }
        }

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

    /// Access the transition recorder if enabled
    pub fn recorder(&self) -> Option<&TransitionRecorder> {
        self.recorder.as_ref()
    }

    /// Get tools used across all transitions
    ///
    /// Note: This currently returns an empty vector because ParsedSession
    /// doesn't implement Clone, so session data is lost when transitions
    /// are stored. Tool extraction from transitions requires the parsed
    /// session data which isn't preserved during cloning.
    pub fn tools_used(&self) -> Vec<String> {
        let mut tools = std::collections::HashSet::new();
        for transition in &self.transitions {
            // Extract tools from transition's tool executions
            for tool_exec in transition.tool_executions() {
                tools.insert(tool_exec.tool_name.clone());
            }
        }
        let mut result: Vec<String> = tools.into_iter().collect();
        result.sort();
        result
    }

    /// Save conversation to disk
    pub fn save(&self, path: &std::path::Path) -> Result<(), ConversationError> {
        let saved = SavedConversation {
            id: self.id,
            transitions: self.transitions.clone(),
            session_ids: self.session_ids.clone(),
            metadata: self.metadata.clone(),
            recording_enabled: self.recorder.is_some(),
        };
        let data = serde_json::to_string_pretty(&saved)?;
        std::fs::write(path, data)?;
        Ok(())
    }

    /// Load conversation from disk
    pub fn load(
        path: &std::path::Path,
        workspace: Arc<Workspace>,
        record: bool,
    ) -> Result<Self, ConversationError> {
        let data = std::fs::read_to_string(path)?;
        let saved: SavedConversation = serde_json::from_str(&data)?;

        let record = if record {
            true
        } else {
            saved.recording_enabled
        };
        let recorder = if record {
            Some(TransitionRecorder::new(workspace.path())?)
        } else {
            None
        };

        Ok(Self {
            id: saved.id,
            workspace,
            transitions: saved.transitions,
            session_ids: saved.session_ids,
            metadata: saved.metadata,
            recorder,
        })
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

    #[error("Recorder error: {0}")]
    RecorderError(#[from] RecorderError),

    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}
