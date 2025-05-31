use pyo3::prelude::*;
use crate::types::{ContentBlock, MessageRecord as RustMessageRecord, ParsedSession as RustParsedSession};
use crate::python::models::{TextBlock, ToolUseBlock, ThinkingBlock, ImageBlock, ToolResultBlock};

fn content_block_to_py(py: Python<'_>, block: &ContentBlock) -> PyObject {
    match block {
        ContentBlock::Text { text } => Py::new(py, TextBlock { text: text.clone() }).unwrap().into(),
        ContentBlock::Thinking { thinking, signature } => Py::new(py, ThinkingBlock { thinking: thinking.clone(), signature: signature.clone() }).unwrap().into(),
        ContentBlock::ToolUse { id, name, input } => Py::new(py, ToolUseBlock::from_content_block(id.clone(), name.clone(), input.clone())).unwrap().into(),
        ContentBlock::ToolResult { tool_use_id, content, is_error } => Py::new(py, ToolResultBlock { tool_use_id: tool_use_id.clone(), content: content.as_ref().map(|c| c.as_text()), is_error: *is_error }).unwrap().into(),
        ContentBlock::Image { source } => Py::new(py, ImageBlock { source_type: source.source_type.clone(), media_type: source.media_type.clone(), data: source.data.clone() }).unwrap().into(),
    }
}
use std::collections::HashMap;

/// Individual message in a Claude Code conversation.
/// 
/// This class represents a single message in a Claude Code conversation,
/// with properties for accessing message content, role, cost, and other
/// attributes.
/// 
/// Properties:
///     role: Role of the message sender ("user" or "assistant")
///     text: Text content of the message
///     cost: Cost of the message in USD (None if not available)
///     tools: List of tool names used in this message
///     timestamp: When the message was sent
///     uuid: Unique message identifier  
///     parent_uuid: Parent message UUID for threading (None if root)
///     is_sidechain: Whether this message is part of a sidechain
///     cwd: Working directory path for this message
/// 
/// Example:
///     >>> session = load("conversation.jsonl")
///     >>> for msg in session.messages:
///     ...     print(f"{msg.role}: {msg.text[:50]}...")
///     ...     if msg.cost:
///     ...         print(f"  Cost: ${msg.cost:.4f}")
#[pyclass(name = "Message", module = "claude_sdk")]
#[derive(Clone)]
pub struct Message {
    #[pyo3(get)]
    pub role: String,
    #[pyo3(get)]
    pub text: String,
    #[pyo3(get)]
    pub model: Option<String>,
    #[pyo3(get)]
    pub cost: Option<f64>,
    #[pyo3(get)]
    pub tools: Vec<String>,
    #[pyo3(get)]
    pub stop_reason: Option<String>,
    #[pyo3(get)]
    pub usage: Option<crate::python::models::TokenUsage>,
    #[pyo3(get)]
    pub timestamp: String,
    #[pyo3(get)]
    pub uuid: String,
    #[pyo3(get)]
    pub parent_uuid: Option<String>,
    #[pyo3(get)]
    pub is_sidechain: bool,
    #[pyo3(get)]
    pub cwd: String,
    // Store the raw content for get_tool_blocks
    content_blocks: Vec<ContentBlock>,
}

#[pymethods]
impl Message {
    fn __repr__(&self) -> String {
        format!("<Message role='{}' uuid='{}' cost={:?}>", 
            self.role, self.uuid, self.cost)
    }
    
    fn __str__(&self) -> String {
        format!("{}: {}", self.role, self.text)
    }
    
    /// Get all tool use blocks in this message.
    /// 
    /// Returns:
    ///     List[ToolUseBlock]: List of tool use blocks
    fn get_tool_blocks(&self) -> Vec<crate::python::models::ToolUseBlock> {
        let mut blocks = Vec::new();
        for content in &self.content_blocks {
            if let ContentBlock::ToolUse { id, name, input } = content {
                blocks.push(crate::python::models::ToolUseBlock::from_content_block(
                    id.clone(),
                    name.clone(),
                    input.clone(),
                ));
            }
        }
        blocks
    }

    /// Get all content blocks with proper typing.
    fn get_content_blocks(&self, py: Python<'_>) -> Vec<PyObject> {
        self.content_blocks
            .iter()
            .map(|b| content_block_to_py(py, b))
            .collect()
    }
}

impl Message {
    pub fn from_rust_message(msg: &RustMessageRecord) -> Self {
        let role = format!("{:?}", msg.message.role).to_lowercase();
        
        // Extract text content and tools
        let mut text_parts = Vec::new();
        let mut tools = Vec::new();
        
        for content in &msg.message.content {
            match content {
                ContentBlock::Text { text } => {
                    text_parts.push(text.clone());
                }
                ContentBlock::ToolUse { name, .. } => {
                    tools.push(name.clone());
                }
                _ => {}
            }
        }
        
        Message {
            role,
            text: text_parts.join("\n"),
            model: msg.message.model.clone(),
            cost: Some(msg.cost()),
            tools,
            stop_reason: msg.message.stop_reason.as_ref().map(|s| match s {
                crate::types::StopReason::EndTurn => "end_turn".to_string(),
                crate::types::StopReason::MaxTokens => "max_tokens".to_string(),
                crate::types::StopReason::StopSequence => "stop_sequence".to_string(),
                crate::types::StopReason::ToolUse => "tool_use".to_string(),
                crate::types::StopReason::Error => "error".to_string(),
            }),
            usage: msg.message.usage.as_ref().map(|u| crate::python::models::TokenUsage{
                input_tokens: u.input_tokens,
                cache_creation_input_tokens: u.cache_creation_input_tokens,
                cache_read_input_tokens: u.cache_read_input_tokens,
                output_tokens: u.output_tokens,
                service_tier: u.service_tier.clone(),
            }),
            timestamp: msg.timestamp.to_rfc3339(),
            uuid: msg.uuid.to_string(),
            parent_uuid: msg.parent_uuid.as_ref().map(|u| u.to_string()),
            is_sidechain: msg.is_sidechain,
            cwd: msg.cwd.to_string_lossy().to_string(),
            content_blocks: msg.message.content.clone(),
        }
    }
}

/// Primary container for Claude Code session data.
/// 
/// This class represents a complete Claude Code session, containing messages,
/// conversation threading, tool usage information, and metadata.
/// 
/// Properties:
///     session_id: Unique identifier for the session
///     messages: List of Message objects in conversation order
///     total_cost: Total USD cost of the session
///     tools_used: Set of tool names used in the session
///     duration: Total session duration in seconds (None if not available)
///     tool_costs: Cost breakdown by tool (dict mapping tool name to cost)
///     cost_by_turn: Cost breakdown by message turn (list of costs)
///     conversation_tree: ConversationTree object showing message relationships
///     metadata: SessionMetadata object with detailed statistics
///     tool_executions: List of ToolExecution objects
/// 
/// Methods:
///     get_main_chain(): Get only the main conversation messages (no sidechains)
///     get_messages_by_role(role): Get messages with a specific role
/// 
/// Example:
///     >>> session = load("conversation.jsonl")
///     >>> print(f"Session ID: {session.session_id}")
///     >>> print(f"Total cost: ${session.total_cost:.4f}")
///     >>> print(f"Tools used: {', '.join(session.tools_used)}")
///     >>> 
///     >>> # Get only user messages
///     >>> user_msgs = session.get_messages_by_role("user")
///     >>> print(f"User messages: {len(user_msgs)}")
#[pyclass(name = "Session", module = "claude_sdk")]
pub struct Session {
    #[pyo3(get)]
    pub session_id: String,
    #[pyo3(get)]
    pub messages: Vec<Message>,
    #[pyo3(get)]
    pub total_cost: f64,
    #[pyo3(get)]
    pub tools_used: Vec<String>,
    #[pyo3(get)]
    pub duration: Option<i64>,
    #[pyo3(get)]
    pub conversation_tree: crate::python::models::ConversationTree,
    #[pyo3(get)]
    pub metadata: crate::python::models::SessionMetadata,
    #[pyo3(get)]
    pub tool_executions: Vec<crate::python::models::ToolExecution>,
    pub inner: RustParsedSession,
}

#[pymethods]
impl Session {
    #[getter]
    fn tool_costs(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);
        for (tool, count) in &self.inner.metadata.tool_usage_count {
            // Simple cost distribution based on usage count
            let tool_cost = if self.inner.metadata.total_tool_calls > 0 {
                self.total_cost * (*count as f64) / (self.inner.metadata.total_tool_calls as f64)
            } else {
                0.0
            };
            dict.set_item(tool, tool_cost)?;
        }
        Ok(dict.into())
    }
    
    #[getter]
    fn project_path(&self) -> PyResult<String> {
        // Get project path from the first message's cwd
        if self.inner.messages.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Cannot determine project path from empty session"
            ));
        }
        Ok(self.inner.messages[0].cwd.to_string_lossy().to_string())
    }
    
    #[getter]
    fn project_name(&self) -> PyResult<String> {
        // Get project name from the project path
        if self.inner.messages.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Cannot determine project name from empty session"
            ));
        }
        let project_path = &self.inner.messages[0].cwd;
        let name = project_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");
        Ok(name.to_string())
    }
    
    #[getter]
    fn cost_by_turn(&self) -> Vec<f64> {
        self.messages.iter()
            .map(|msg| msg.cost.unwrap_or(0.0))
            .collect()
    }
    
    /// Get only the main conversation chain (excluding sidechains).
    /// 
    /// Returns:
    ///     List[Message]: Messages in the main conversation thread
    fn get_main_chain(&self) -> Vec<Message> {
        self.messages.iter()
            .filter(|msg| !msg.is_sidechain)
            .cloned()
            .collect()
    }
    
    /// Get messages with a specific role.
    /// 
    /// Args:
    ///     role: Role to filter by ("user" or "assistant")
    /// 
    /// Returns:
    ///     List[Message]: Messages with the specified role
    fn get_messages_by_role(&self, role: &str) -> Vec<Message> {
        self.messages.iter()
            .filter(|msg| msg.role == role)
            .cloned()
            .collect()
    }
    
    fn __repr__(&self) -> String {
        format!("<Session id='{}' messages={} cost=${:.4}>",
            self.session_id, self.messages.len(), self.total_cost)
    }
}

impl Session {
    pub fn from_rust_session(session: RustParsedSession) -> Self {
        let messages: Vec<Message> = session.messages.iter()
            .map(Message::from_rust_message)
            .collect();
        
        let duration = session.metadata.session_duration
            .map(|d| d.num_seconds());
        
        // Convert metadata
        let metadata = crate::python::models::SessionMetadata::from_rust_metadata(&session.metadata);
        
        // Convert conversation tree
        let conversation_tree = crate::python::models::ConversationTree::from_rust_tree(&session.conversation_tree);
        
        // Extract tool executions from messages
        let tool_executions = extract_tool_executions(&session.messages);
        
        Session {
            session_id: session.session_id.to_string(),
            total_cost: session.metadata.total_cost_usd,
            tools_used: session.metadata.unique_tools_used.clone(),
            duration,
            messages,
            conversation_tree,
            metadata,
            tool_executions,
            inner: session,
        }
    }
}

// Helper function to extract tool executions from messages
fn extract_tool_executions(messages: &[RustMessageRecord]) -> Vec<crate::python::models::ToolExecution> {
    use std::collections::HashMap;
    use crate::types::{ContentBlock, ToolResult, ToolExecution};
    
    let mut tool_executions = Vec::new();
    let mut pending_tools: HashMap<String, (String, serde_json::Value, chrono::DateTime<chrono::Utc>)> = HashMap::new();
    
    for message in messages {
        for content in &message.message.content {
            match content {
                ContentBlock::ToolUse { id, name, input } => {
                    pending_tools.insert(id.clone(), (name.clone(), input.clone(), message.timestamp));
                }
                ContentBlock::ToolResult { tool_use_id, content, is_error } => {
                    if let Some((tool_name, input, start_time)) = pending_tools.remove(tool_use_id) {
                        let duration = std::time::Duration::from_millis(
                            (message.timestamp - start_time).num_milliseconds().max(0) as u64
                        );
                        
                        let tool_result = ToolResult {
                            tool_use_id: tool_use_id.clone(),
                            content: content.as_ref().map(|c| c.as_text()).unwrap_or_default(),
                            stdout: None,
                            stderr: None,
                            interrupted: false,
                            is_error: is_error.unwrap_or(false),
                            metadata: serde_json::Value::Null,
                        };
                        
                        let rust_exec = ToolExecution::new(
                            tool_name,
                            input,
                            tool_result,
                            duration,
                            message.timestamp,
                        );
                        
                        tool_executions.push(crate::python::models::ToolExecution::from_rust_execution(&rust_exec));
                    }
                }
                _ => {}
            }
        }
    }
    
    tool_executions
}

/// Container for a Claude Code project with multiple sessions.
/// 
/// This class represents a Claude Code project directory containing multiple
/// session files. It provides aggregate statistics across all sessions in
/// the project.
/// 
/// Properties:
///     name: Project name (derived from directory name)
///     sessions: List of Session objects for this project
///     total_cost: Total cost across all sessions
///     total_messages: Total number of messages across all sessions
///     tool_usage_count: Aggregate tool usage counts across sessions
///     total_duration: Total duration across all sessions (if available)
/// 
/// Example:
///     >>> project = load_project("apply-model")
///     >>> print(f"Project: {project.name}")
///     >>> print(f"Sessions: {len(project.sessions)}")
///     >>> print(f"Total cost: ${project.total_cost:.4f}")
///     >>> 
///     >>> # Analyze tool usage
///     >>> for tool, count in project.tool_usage_count.items():
///     ...     print(f"{tool}: {count} uses")
#[pyclass(name = "Project", module = "claude_sdk")]
pub struct Project {
    #[pyo3(get)]
    pub name: String,
    // Store sessions as PyObject to avoid Clone requirement
    sessions_py: Py<pyo3::types::PyList>,
    sessions_count: usize,
    #[pyo3(get)]
    pub total_cost: f64,
    #[pyo3(get)]
    pub total_messages: usize,
    #[pyo3(get)]
    pub tool_usage_count: HashMap<String, usize>,
    #[pyo3(get)]
    pub total_duration: Option<i64>,  // Total duration in seconds
}

#[pymethods]
impl Project {
    #[getter]
    fn sessions(&self, py: Python<'_>) -> PyObject {
        self.sessions_py.clone_ref(py).into()
    }
    
    fn __repr__(&self) -> String {
        format!("<Project name='{}' sessions={} cost=${:.4}>",
            self.name, self.sessions_count, self.total_cost)
    }
    
    fn __str__(&self) -> String {
        format!("Project '{}' with {} sessions", self.name, self.sessions_count)
    }
}

impl Project {
    pub fn new(py: Python<'_>, name: String, sessions: Vec<Session>) -> PyResult<Self> {
        // Calculate aggregate statistics
        let mut total_cost = 0.0;
        let mut total_messages = 0;
        let mut tool_usage_count: HashMap<String, usize> = HashMap::new();
        let mut total_duration_secs = 0i64;
        let mut has_duration = false;
        
        for session in &sessions {
            total_cost += session.total_cost;
            total_messages += session.messages.len();
            
            // Aggregate tool usage from the inner Rust session
            for (tool, count) in &session.inner.metadata.tool_usage_count {
                *tool_usage_count.entry(tool.clone()).or_insert(0) += count;
            }
            
            // Add duration if available
            if let Some(duration) = session.duration {
                total_duration_secs += duration;
                has_duration = true;
            }
        }
        
        // Create Python list of sessions
        let sessions_list = pyo3::types::PyList::empty(py);
        let sessions_count = sessions.len();
        for session in sessions {
            // Convert each Session to a PyObject
            let session_obj = Py::new(py, session)?;
            sessions_list.append(session_obj)?;
        }
        
        Ok(Project {
            name,
            sessions_py: sessions_list.into(),
            sessions_count,
            total_cost,
            total_messages,
            tool_usage_count,
            total_duration: if has_duration { Some(total_duration_secs) } else { None },
        })
    }
}