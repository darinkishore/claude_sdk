//! Workspace provides infrastructure for Claude execution
//!
//! This is a simplified version of the former ClaudeEnvironment,
//! containing only the executor and observer. Transition recording
//! is now handled by Conversation.

use std::path::PathBuf;
use crate::execution::{
    ClaudeExecutor, ExecutorError,
    EnvironmentObserver, EnvironmentSnapshot, ObserverError,
};

/// Workspace provides the infrastructure for executing Claude commands
/// and observing the filesystem state. It does not manage conversations
/// or record transitions - that's handled by the Conversation abstraction.
pub struct Workspace {
    pub(crate) executor: ClaudeExecutor,
    pub(crate) observer: EnvironmentObserver,
    workspace_path: PathBuf,
}

impl Workspace {
    /// Create a new workspace at the given path
    pub fn new(workspace_path: PathBuf) -> Result<Self, WorkspaceError> {
        let executor = ClaudeExecutor::new(workspace_path.clone())?;
        let observer = EnvironmentObserver::new(workspace_path.clone());
        
        Ok(Self {
            executor,
            observer,
            workspace_path,
        })
    }
    
    /// Get the workspace path
    pub fn path(&self) -> &PathBuf {
        &self.workspace_path
    }
    
    /// Take a snapshot of the current workspace state
    pub fn snapshot(&self) -> Result<EnvironmentSnapshot, WorkspaceError> {
        self.observer.snapshot()
            .map_err(WorkspaceError::ObserverError)
    }
    
    /// Take a snapshot with a specific session ID
    pub fn snapshot_with_session(&self, session_id: &str) -> Result<EnvironmentSnapshot, WorkspaceError> {
        self.observer.snapshot_with_session(session_id)
            .map_err(WorkspaceError::ObserverError)
    }
}

#[derive(Debug, thiserror::Error)]
pub enum WorkspaceError {
    #[error("Executor error: {0}")]
    ExecutorError(#[from] ExecutorError),
    
    #[error("Observer error: {0}")]
    ObserverError(#[from] ObserverError),
}