use std::path::PathBuf;
use uuid::Uuid;
use crate::execution::{
    ClaudeExecutor, ClaudePrompt, ExecutorError,
    EnvironmentObserver, ObserverError,
    TransitionRecorder, Transition, RecorderError,
};

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
            recorded_at: chrono::Utc::now(),
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
    
    pub fn workspace(&self) -> &PathBuf {
        &self.workspace
    }
}

#[derive(Debug, thiserror::Error)]
pub enum EnvironmentError {
    #[error("Executor error: {0}")]
    ExecutorError(#[from] ExecutorError),
    
    #[error("Observer error: {0}")]
    ObserverError(#[from] ObserverError),
    
    #[error("Recorder error: {0}")]
    RecorderError(#[from] RecorderError),
}