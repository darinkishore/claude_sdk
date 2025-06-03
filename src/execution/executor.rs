use std::process::Command;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudePrompt {
    pub text: String,
    pub continue_session: bool,
    #[serde(default)]
    pub resume_session_id: Option<String>,  // Explicit session to resume
}

impl Default for ClaudePrompt {
    fn default() -> Self {
        Self {
            text: String::new(),
            continue_session: false,
            resume_session_id: None,
        }
    }
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

/// Default tools that Claude Code has access to
const DEFAULT_ALLOWED_TOOLS: &str = "Task,Bash,Glob,Grep,LS,Read,Edit,MultiEdit,Write,NotebookRead,NotebookEdit,WebFetch,TodoRead,TodoWrite,WebSearch";

pub struct ClaudeExecutor {
    claude_binary: PathBuf,
    working_directory: PathBuf,
    allowed_tools: Option<String>,
    disallowed_tools: Option<String>,
    skip_permissions: bool,
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
            skip_permissions: false,  // Don't skip by default
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
    
    /// Enable dangerous mode that skips all permission checks
    /// This should only be used in tests or when explicitly requested
    pub fn set_skip_permissions(&mut self, skip: bool) {
        self.skip_permissions = skip;
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
        
        // Handle tool permissions
        if self.skip_permissions {
            // Explicitly skip permissions (for tests)
            cmd.arg("--dangerously-skip-permissions");
        } else if self.allowed_tools.is_some() || self.disallowed_tools.is_some() {
            // Use explicit permissions if set
            if let Some(ref allowed) = self.allowed_tools {
                cmd.arg("--allowedTools").arg(allowed);
            }
            if let Some(ref disallowed) = self.disallowed_tools {
                cmd.arg("--disallowedTools").arg(disallowed);
            }
        } else {
            // Default: use standard Claude Code tools
            cmd.arg("--allowedTools").arg(DEFAULT_ALLOWED_TOOLS);
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
            tool_calls: extract_tool_calls(&self.working_directory, &response),
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

use crate::parser::SessionParser;
use crate::utils::path::encode_project_path;
use crate::types::ContentBlock;

fn extract_tool_calls(workspace: &std::path::Path, response: &ClaudeJsonResponse) -> Vec<String> {
    let home = match home::home_dir() {
        Some(h) => h,
        None => return Vec::new(),
    };

    let project_dir = home
        .join(".claude")
        .join("projects")
        .join(encode_project_path(workspace));

    let session_file = project_dir.join(format!("{}.jsonl", response.session_id));
    let parser = SessionParser::new(&session_file);

    match parser.parse() {
        Ok(session) => {
            let mut tools = std::collections::HashSet::new();
            for msg in session.messages {
                for block in msg.message.content {
                    if let ContentBlock::ToolUse { name, .. } = block {
                        tools.insert(name);
                    }
                }
            }
            let mut result: Vec<String> = tools.into_iter().collect();
            result.sort();
            result
        }
        Err(_) => Vec::new(),
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;
    use std::path::PathBuf;

    #[test]
    fn test_extract_tool_calls_from_fixture() {
        // Setup temporary HOME to mimic Claude project layout
        let tmp_home = tempdir().unwrap();
        std::env::set_var("HOME", tmp_home.path());

        // Workspace path from fixture
        let workspace = PathBuf::from("/home/test/project");
        let project_dir = tmp_home
            .path()
            .join(".claude")
            .join("projects")
            .join(encode_project_path(&workspace));
        fs::create_dir_all(&project_dir).unwrap();

        // Copy fixture session file to expected location
        let session_file = project_dir.join("sess1.jsonl");
        fs::copy("tests/fixtures/example_sample.jsonl", &session_file).unwrap();

        // Build fake response
        let response = ClaudeJsonResponse {
            result: String::new(),
            session_id: "sess1".to_string(),
            cost_usd: 0.0,
            model: None,
            total_cost: 0.0,
            duration_ms: 0,
        };

        let tools = extract_tool_calls(&workspace, &response);
        assert_eq!(tools, vec!["echo".to_string()]);
    }
}