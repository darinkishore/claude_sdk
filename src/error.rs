use std::path::PathBuf;
use std::time::Duration;
use thiserror::Error;

/// Main error type for the Claude Code SDK
#[derive(Debug, Error)]
pub enum ClaudeError {
    #[error("Session not found: {session_id}")]
    SessionNotFound { session_id: String },
    
    #[error("Parse error: {0}")]
    ParseError(#[from] ParseError),
    
    #[error("Execution error: {0}")]
    ExecutionError(#[from] ExecutionError),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::Error),
}

/// Errors that can occur during JSONL parsing
#[derive(Debug, Error)]
pub enum ParseError {
    #[error("Invalid JSONL format at line {line}: {message}")]
    InvalidJsonl { line: usize, message: String },
    
    #[error("Missing required field '{field}' in record")]
    MissingField { field: String },
    
    #[error("Invalid timestamp format: {0}")]
    InvalidTimestamp(String),
    
    #[error("Invalid UUID format: {0}")]
    InvalidUuid(String),
    
    #[error("Corrupted session file: {reason}")]
    CorruptedFile { reason: String },
    
    #[error("Empty session file")]
    EmptyFile,
    
    #[error("Unsupported format version: {version}")]
    UnsupportedVersion { version: String },
}

/// Errors that can occur during Claude execution
#[derive(Debug, Error)]
pub enum ExecutionError {
    #[error("Claude binary not found at: {path}")]
    ClaudeBinaryNotFound { path: PathBuf },
    
    #[error("Claude execution failed: {stderr}")]
    ClaudeFailure { stderr: String, exit_code: Option<i32> },
    
    #[error("Invalid output format: {0}")]
    InvalidOutput(String),
    
    #[error("Timeout after {duration:?}")]
    Timeout { duration: Duration },
    
    #[error("Process spawn failed: {0}")]
    ProcessSpawn(#[source] std::io::Error),
}