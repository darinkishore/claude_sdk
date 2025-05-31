use pyo3::prelude::*;

pub mod classes;
pub mod exceptions;
pub mod functions;
pub mod models;
pub mod utils;

use classes::{Message, Session, Project};
use models::{SessionMetadata, ToolResult, ToolExecution, ConversationStats, ConversationNode, ConversationTree, TextBlock, ToolUseBlock, ThinkingBlock, ImageBlock, ToolResultBlock, TokenUsage};
use exceptions::register_exceptions;
use functions::{load, find_sessions, find_projects, load_project};

pub fn register_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add classes
    m.add_class::<Message>()?;
    m.add_class::<Session>()?;
    m.add_class::<Project>()?;
    
    // Add model classes
    m.add_class::<SessionMetadata>()?;
    m.add_class::<ToolResult>()?;
    m.add_class::<ToolExecution>()?;
    m.add_class::<ConversationStats>()?;
    m.add_class::<ConversationNode>()?;
    m.add_class::<ConversationTree>()?;
    m.add_class::<TextBlock>()?;
    m.add_class::<ToolUseBlock>()?;
    m.add_class::<ThinkingBlock>()?;
    m.add_class::<ImageBlock>()?;
    m.add_class::<ToolResultBlock>()?;
    m.add_class::<TokenUsage>()?;
    
    // Add exceptions
    register_exceptions(m)?;
    
    // Add functions
    m.add_function(pyo3::wrap_pyfunction!(load, m)?)?;
    m.add_function(pyo3::wrap_pyfunction!(find_sessions, m)?)?;
    m.add_function(pyo3::wrap_pyfunction!(find_projects, m)?)?;
    m.add_function(pyo3::wrap_pyfunction!(load_project, m)?)?;
    
    Ok(())
}