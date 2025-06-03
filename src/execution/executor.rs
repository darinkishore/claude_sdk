use std::process::Command;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudePrompt {
    pub text: String,
    pub continue_session: bool,
    pub resume_session_id: Option<String>,  // Explicit session to resume
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
    allowed_tools: Option<String>,
    disallowed_tools: Option<String>,
}

impl ClaudeExecutor {
    pub fn new(working_directory: PathBuf) -> Result<Self, ExecutorError> {
        // Find claude binary
        let claude_binary = which::which("claude")
            .map_err(|_| ExecutorError::ClaudeNotFound)?;
        
        Ok(Self {
            claude_binary,
            working_directory,
            allowed_tools: None,
            disallowed_tools: None,
        })
    }
    
    /// Set allowed tools (e.g., "Read,Write" or "Bash(npm install)" or "*")
    pub fn set_allowed_tools(&mut self, tools: Option<String>) {
        self.allowed_tools = tools;
    }
    
    /// Set disallowed tools (e.g., "Bash(rm -rf)" or "Write")
    pub fn set_disallowed_tools(&mut self, tools: Option<String>) {
        self.disallowed_tools = tools;
    }
    
    pub fn execute(&self, prompt: ClaudePrompt) -> Result<ClaudeExecution, ExecutorError> {
        let start = std::time::Instant::now();
        
        // Build command
        let mut cmd = Command::new(&self.claude_binary);
        cmd.current_dir(&self.working_directory);  // Claude tracks sessions per directory
        
        // Add flags (order matters for some)
        cmd.arg("--output-format").arg("json");
        
        // Session management
        if let Some(ref session_id) = prompt.resume_session_id {
            cmd.arg("--resume").arg(session_id);
        } else if prompt.continue_session {
            cmd.arg("--continue");
        }
        
        // Add tool permissions or skip them entirely
        if self.allowed_tools.is_some() || self.disallowed_tools.is_some() {
            // Use explicit permissions if set
            if let Some(ref allowed) = self.allowed_tools {
                cmd.arg("--allowedTools").arg(allowed);
            }
            if let Some(ref disallowed) = self.disallowed_tools {
                cmd.arg("--disallowedTools").arg(disallowed);
            }
        } else {
            // Default: skip permissions entirely
            cmd.arg("--dangerously-skip-permissions");
        }
        
        // -p must come right before the prompt text
        cmd.arg("-p");
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
    #[allow(dead_code)]
    total_cost: f64,
    #[serde(default)]
    #[allow(dead_code)]
    duration_ms: u64,
}

fn extract_tool_calls(_response: &ClaudeJsonResponse) -> Vec<String> {
    // Tool calls are now extracted from ParsedSession after execution
    // This placeholder remains for backward compatibility
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