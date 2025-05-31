//! # Claude Code SDK
//!
//! A Rust library for parsing and analyzing Claude Code session data.
//! Provides efficient access to Claude Code's JSONL format with conversation
//! threading, tool usage extraction, and performance metrics.

pub mod types;
pub mod parser;
pub mod conversation;
pub mod error;
pub mod utils;

// Re-export main types for convenience
pub use types::{
    // Message types
    MessageRecord, Message, TokenUsage,
    // Content types
    ContentBlock, ToolResultContent, ImageSource,
    // Enums
    Role, MessageType, UserType, StopReason, OutputFormat,
    // Session types
    SessionId, SessionConfig, SessionMetadata, ParsedSession, SummaryRecord,
    // Tool types
    ToolResult, ToolExecution,
};

pub use parser::SessionParser;
pub use conversation::{ConversationTree, ConversationNode};
pub use error::{ClaudeError, ParseError, ExecutionError};

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