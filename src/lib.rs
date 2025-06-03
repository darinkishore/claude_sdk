//! # Claude Code SDK
//!
//! A Rust library for parsing and analyzing Claude Code session data.
//! Provides efficient access to Claude Code's JSONL format with conversation
//! threading, tool usage extraction, and performance metrics.

pub mod conversation;
pub mod error;
pub mod parser;
pub mod types;
pub mod utils;
pub mod execution;

// Re-export main types for convenience
pub use types::{
    // Content types
    ContentBlock,
    ImageSource,
    Message,
    // Message types
    MessageRecord,
    MessageType,
    OutputFormat,
    ParsedSession,
    // Enums
    Role,
    SessionConfig,
    // Session types
    SessionId,
    SessionMetadata,
    StopReason,
    SummaryRecord,
    TokenUsage,
    ToolExecution,
    // Tool types
    ToolResult,
    ToolResultContent,
    UserType,
};

pub use conversation::{ConversationNode, ConversationTree};
pub use error::{ClaudeError, ExecutionError, ParseError};
pub use parser::SessionParser;

/// Result type alias for the library
pub type Result<T> = std::result::Result<T, ClaudeError>;

// Python bindings module
#[cfg(feature = "python")]
mod python;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    python::register_module(m)?;
    Ok(())
}
