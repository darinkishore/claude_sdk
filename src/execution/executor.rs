use std::process::Command;
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
        cmd.current_dir(&self.working_directory)  // Claude tracks sessions per directory
           .arg("-p")  // Programmatic mode
           .arg("--output-format").arg("json")
           .arg("--dangerously-skip-permissions");  // Skip permission prompts for automation
           
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
            response: response.result.clone(),
            session_id: response.session_id.clone(),
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

fn extract_tool_calls(_response: &ClaudeJsonResponse) -> Vec<String> {
    // TODO: Parse tool calls from result text or wait for better API
    // For now, we'll extract them when we parse the session
    Vec::new()
}

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