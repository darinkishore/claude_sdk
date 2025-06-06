//! Workspace provides infrastructure for Claude execution
//!
//! This is a simplified version of the former ClaudeEnvironment,
//! containing only the executor and observer. Transition recording
//! is now handled by Conversation.

use std::path::PathBuf;
use std::collections::HashMap;
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
        // Ensure the workspace directory exists so subsequent operations succeed
        std::fs::create_dir_all(&workspace_path)
            .map_err(|e| WorkspaceError::ObserverError(ObserverError::IoError(e.to_string())))?;

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

    /// Capture only the workspace files without session data
    pub fn snapshot_files(&self) -> Result<HashMap<PathBuf, String>, WorkspaceError> {
        self.observer.snapshot_files()
            .map_err(WorkspaceError::ObserverError)
    }
    
    /// Take a snapshot with a specific session ID
    pub fn snapshot_with_session(&self, session_id: &str) -> Result<EnvironmentSnapshot, WorkspaceError> {
        self.observer.snapshot_with_session(session_id)
            .map_err(WorkspaceError::ObserverError)
    }
    
    /// Configure tool permissions for the executor
    pub fn set_allowed_tools(&mut self, tools: Option<String>) {
        self.executor.set_allowed_tools(tools);
    }
    
    /// Configure disallowed tools for the executor
    pub fn set_disallowed_tools(&mut self, tools: Option<String>) {
        self.executor.set_disallowed_tools(tools);
    }
    
    /// Enable dangerous mode that skips all permission checks
    /// This should only be used in tests or when explicitly requested
    pub fn set_skip_permissions(&mut self, skip: bool) {
        self.executor.set_skip_permissions(skip);
    }
    
    /// Set the model to use for Claude execution
    /// Set to None to use Claude's default model
    pub fn set_model(&mut self, model: Option<String>) {
        self.executor.set_model(model);
    }
}

#[derive(Debug, thiserror::Error)]
pub enum WorkspaceError {
    #[error("Executor error: {0}")]
    ExecutorError(#[from] ExecutorError),
    
    #[error("Observer error: {0}")]
    ObserverError(#[from] ObserverError),
}