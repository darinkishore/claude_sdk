use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::time::Duration;

/// Result from a tool execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    pub tool_use_id: String,
    pub content: String,
    pub stdout: Option<String>,
    pub stderr: Option<String>,
    pub interrupted: bool,
    pub is_error: bool,
    pub metadata: serde_json::Value, // Tool-specific rich data
}

/// Represents a complete tool execution with timing
#[derive(Debug, Clone)]
pub struct ToolExecution {
    pub tool_name: String,
    pub input: serde_json::Value,
    pub output: ToolResult,
    pub duration: Duration,
    pub timestamp: DateTime<Utc>,
}

impl ToolResult {
    /// Check if this tool execution was successful
    pub fn is_success(&self) -> bool {
        !self.is_error && !self.interrupted
    }
    
    /// Get the effective output content
    pub fn effective_content(&self) -> &str {
        if self.is_error && !self.stderr.as_ref().unwrap_or(&String::new()).is_empty() {
            self.stderr.as_ref().unwrap()
        } else if !self.stdout.as_ref().unwrap_or(&String::new()).is_empty() {
            self.stdout.as_ref().unwrap()
        } else {
            &self.content
        }
    }
}

impl ToolExecution {
    /// Create a new tool execution record
    pub fn new(
        tool_name: String,
        input: serde_json::Value,
        output: ToolResult,
        duration: Duration,
        timestamp: DateTime<Utc>,
    ) -> Self {
        Self {
            tool_name,
            input,
            output,
            duration,
            timestamp,
        }
    }
    
    /// Check if this tool execution was successful
    pub fn is_success(&self) -> bool {
        self.output.is_success()
    }
    
    /// Get the tool execution duration in milliseconds
    pub fn duration_ms(&self) -> u64 {
        self.duration.as_millis() as u64
    }
}