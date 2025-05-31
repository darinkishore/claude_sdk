use pyo3::prelude::*;
use crate::types::{ContentBlock, MessageRecord as RustMessageRecord, ParsedSession as RustParsedSession, TokenUsage};
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
///     total_tokens: Total tokens used (input + output) if available
///     input_tokens: Input tokens used if available
///     output_tokens: Output tokens generated if available
///     stop_reason: Reason why generation stopped if available
///     model: Model used for this message if available
/// 
/// Methods:
///     get_tool_blocks(): Get all tool use blocks in this message
///     get_text_blocks(): Get all text content blocks
///     has_tool_use(): Check if message contains tool usage
/// 
/// Example:
///     >>> session = load("conversation.jsonl")
///     >>> for msg in session.messages:
///     ...     print(f"{msg.role}: {msg.text[:50]}...")
///     ...     if msg.cost:
///     ...         print(f"  Cost: ${msg.cost:.4f}")
///     ...     if msg.has_tool_use():
///     ...         print(f"  Tools: {', '.join(msg.tools)}")
#[pyclass(name = "Message", module = "claude_sdk")]
#[derive(Clone)]
pub struct Message {
    #[pyo3(get)]
    pub role: String,
    #[pyo3(get)]
    pub text: String,
    #[pyo3(get)]
    pub cost: Option<f64>,
    #[pyo3(get)]
    pub tools: Vec<String>,
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
    #[pyo3(get)]
    pub total_tokens: Option<u32>,
    #[pyo3(get)]
    pub input_tokens: Option<u32>,
    #[pyo3(get)]
    pub output_tokens: Option<u32>,
    #[pyo3(get)]
    pub stop_reason: Option<String>,
    #[pyo3(get)]
    pub model: Option<String>,
    // Store the raw content for get_tool_blocks
    content_blocks: Vec<ContentBlock>,
    // Store token usage for property access
    token_usage: Option<TokenUsage>,
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
    
    /// Get all text content blocks in this message.
    /// 
    /// Returns:
    ///     List[TextBlock]: List of text content blocks
    /// 
    /// Example:
    ///     >>> text_blocks = msg.get_text_blocks()
    ///     >>> for block in text_blocks:
    ///     ...     print(block.text)
    fn get_text_blocks(&self) -> Vec<crate::python::models::TextBlock> {
        let mut blocks = Vec::new();
        for content in &self.content_blocks {
            if let ContentBlock::Text { text } = content {
                blocks.push(crate::python::models::TextBlock {
                    text: text.clone(),
                });
            }
        }
        blocks
    }
    
    /// Check if this message contains tool usage.
    /// 
    /// Returns:
    ///     bool: True if message contains any tool use blocks
    /// 
    /// Example:
    ///     >>> if msg.has_tool_use():
    ///     ...     print(f"Used tools: {', '.join(msg.tools)}")
    fn has_tool_use(&self) -> bool {
        self.content_blocks.iter().any(|block| matches!(block, ContentBlock::ToolUse { .. }))
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
        
        // Extract token information
        let (total_tokens, input_tokens, output_tokens) = if let Some(usage) = &msg.message.usage {
            (
                Some(usage.input_tokens + usage.output_tokens),
                Some(usage.input_tokens),
                Some(usage.output_tokens),
            )
        } else {
            (None, None, None)
        };
        
        // Convert stop_reason to string if present
        let stop_reason = msg.message.stop_reason.as_ref().map(|sr| format!("{:?}", sr).to_lowercase());
        
        Message {
            role,
            text: text_parts.join("\n"),
            cost: Some(msg.cost()),
            tools,
            timestamp: msg.timestamp.to_rfc3339(),
            uuid: msg.uuid.to_string(),
            parent_uuid: msg.parent_uuid.as_ref().map(|u| u.to_string()),
            is_sidechain: msg.is_sidechain,
            cwd: msg.cwd.to_string_lossy().to_string(),
            total_tokens,
            input_tokens,
            output_tokens,
            stop_reason,
            model: msg.message.model.clone(),
            content_blocks: msg.message.content.clone(),
            token_usage: msg.message.usage.clone(),
        }
    }
}

/// Iterator for messages in a session
#[pyclass(name = "MessageIterator", module = "claude_sdk")]
struct MessageIterator {
    messages: Vec<Message>,
    index: usize,
}

#[pymethods]
impl MessageIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }
    
    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<Message> {
        if slf.index < slf.messages.len() {
            let msg = slf.messages[slf.index].clone();
            slf.index += 1;
            Some(msg)
        } else {
            None
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
///     start_time: Timestamp of the first message (None if not available)
///     end_time: Timestamp of the last message (None if not available)
///     message_count: Total number of messages
///     user_message_count: Number of user messages
///     assistant_message_count: Number of assistant messages
///     root_messages: List of root messages (messages with no parent)
///     conversation_stats: Statistics about the conversation tree
///     tool_costs: Cost breakdown by tool (dict mapping tool name to cost)
///     cost_by_turn: Cost breakdown by message turn (list of costs)
///     conversation_tree: ConversationTree object showing message relationships
///     metadata: SessionMetadata object with detailed statistics
///     tool_executions: List of ToolExecution objects
/// 
/// Methods:
///     get_main_chain(): Get only the main conversation messages (no sidechains)
///     get_messages_by_role(role): Get messages with a specific role
///     get_messages_by_tool(tool_name): Get messages that used a specific tool
///     get_message_by_uuid(uuid): Get a message by its UUID
///     filter_messages(predicate): Filter messages with a custom predicate function
///     get_conversation_tree(): Get the conversation tree structure
///     get_thread(message_uuid): Get all messages in a thread from root to specified message
///     get_all_threads(): Get all conversation threads
///     calculate_metrics(): Calculate various session metrics
///     to_dict(): Convert session to a dictionary
/// 
/// Example:
///     >>> session = load("conversation.jsonl")
///     >>> print(f"Session ID: {session.session_id}")
///     >>> print(f"Total cost: ${session.total_cost:.4f}")
///     >>> print(f"Tools used: {', '.join(session.tools_used)}")
///     >>> print(f"Duration: {session.duration} seconds")
///     >>> 
///     >>> # Get only user messages
///     >>> user_msgs = session.get_messages_by_role("user")
///     >>> print(f"User messages: {len(user_msgs)}")
///     >>> 
///     >>> # Find messages using a specific tool
///     >>> bash_msgs = session.get_messages_by_tool("Bash")
///     >>> print(f"Messages using Bash: {len(bash_msgs)}")
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
    // Additional property getters
    #[getter]
    fn start_time(&self, py: Python<'_>) -> PyResult<PyObject> {
        if let Some(timestamp) = self.inner.metadata.first_message_timestamp {
            crate::python::utils::datetime_to_py(py, timestamp)
        } else {
            Ok(py.None())
        }
    }
    
    #[getter]
    fn end_time(&self, py: Python<'_>) -> PyResult<PyObject> {
        if let Some(timestamp) = self.inner.metadata.last_message_timestamp {
            crate::python::utils::datetime_to_py(py, timestamp)
        } else {
            Ok(py.None())
        }
    }
    
    #[getter]
    fn message_count(&self) -> usize {
        self.messages.len()
    }
    
    #[getter]
    fn user_message_count(&self) -> usize {
        self.inner.metadata.user_messages
    }
    
    #[getter]
    fn assistant_message_count(&self) -> usize {
        self.inner.metadata.assistant_messages
    }
    
    #[getter]
    fn root_messages(&self) -> Vec<Message> {
        self.messages.iter()
            .filter(|msg| msg.parent_uuid.is_none())
            .cloned()
            .collect()
    }
    
    #[getter]
    fn conversation_stats(&self) -> crate::python::models::ConversationStats {
        self.conversation_tree.stats.clone()
    }
    
    #[getter]
    fn tool_costs(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new_bound(py);
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
    
    /// Get messages that used a specific tool.
    /// 
    /// Args:
    ///     tool_name: Name of the tool to filter by
    /// 
    /// Returns:
    ///     List[Message]: Messages that used the specified tool
    fn get_messages_by_tool(&self, tool_name: &str) -> Vec<Message> {
        self.messages.iter()
            .filter(|msg| msg.tools.contains(&tool_name.to_string()))
            .cloned()
            .collect()
    }
    
    /// Get a message by its UUID.
    /// 
    /// Args:
    ///     uuid: UUID string of the message
    /// 
    /// Returns:
    ///     Optional[Message]: The message if found, None otherwise
    fn get_message_by_uuid(&self, uuid: &str) -> Option<Message> {
        self.messages.iter()
            .find(|msg| msg.uuid == uuid)
            .cloned()
    }
    
    /// Filter messages with a custom predicate function.
    /// 
    /// Args:
    ///     predicate: A callable that takes a Message and returns bool
    /// 
    /// Returns:
    ///     List[Message]: Messages that match the predicate
    /// 
    /// Example:
    ///     >>> # Find expensive messages
    ///     >>> expensive = session.filter_messages(lambda m: m.cost and m.cost > 0.01)
    fn filter_messages(&self, predicate: &Bound<'_, PyAny>) -> PyResult<Vec<Message>> {
        let mut filtered = Vec::new();
        for msg in &self.messages {
            let result = predicate.call1((msg.clone(),))?;
            if result.is_truthy()? {
                filtered.push(msg.clone());
            }
        }
        Ok(filtered)
    }
    
    /// Get the conversation tree structure.
    /// 
    /// Returns:
    ///     ConversationTree: The conversation tree object
    fn get_conversation_tree(&self) -> crate::python::models::ConversationTree {
        self.conversation_tree.clone()
    }
    
    /// Get all messages in a thread from root to specified message.
    /// 
    /// Args:
    ///     message_uuid: UUID of the target message
    /// 
    /// Returns:
    ///     List[Message]: Messages in the thread from root to target
    fn get_thread(&self, message_uuid: &str) -> Vec<Message> {
        let mut current_uuid = Some(message_uuid.to_string());
        
        // Build a map for quick lookup
        let uuid_to_msg: HashMap<String, &Message> = self.messages.iter()
            .map(|msg| (msg.uuid.clone(), msg))
            .collect();
        
        // Walk up the parent chain
        let mut path = Vec::new();
        while let Some(uuid) = current_uuid {
            if let Some(msg) = uuid_to_msg.get(&uuid) {
                path.push((*msg).clone());
                current_uuid = msg.parent_uuid.clone();
            } else {
                break;
            }
        }
        
        // Reverse to get root-to-message order
        path.reverse();
        path
    }
    
    /// Get all conversation threads.
    /// 
    /// Returns:
    ///     List[List[Message]]: All threads in the conversation
    fn get_all_threads(&self) -> Vec<Vec<Message>> {
        let mut threads = Vec::new();
        let mut processed_uuids = std::collections::HashSet::new();
        
        // Find all leaf messages (messages with no children)
        let parent_uuids: std::collections::HashSet<String> = self.messages.iter()
            .filter_map(|msg| msg.parent_uuid.as_ref())
            .cloned()
            .collect();
        
        let leaf_messages: Vec<&Message> = self.messages.iter()
            .filter(|msg| !parent_uuids.contains(&msg.uuid))
            .collect();
        
        // Get thread for each leaf message
        for leaf in leaf_messages {
            if !processed_uuids.contains(&leaf.uuid) {
                let thread = self.get_thread(&leaf.uuid);
                // Mark all messages in thread as processed
                for msg in &thread {
                    processed_uuids.insert(msg.uuid.clone());
                }
                if !thread.is_empty() {
                    threads.push(thread);
                }
            }
        }
        
        threads
    }
    
    /// Calculate various session metrics.
    /// 
    /// Returns:
    ///     Dict[str, Any]: Dictionary of calculated metrics
    fn calculate_metrics(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new_bound(py);
        
        // Basic counts
        dict.set_item("total_messages", self.messages.len())?;
        dict.set_item("user_messages", self.user_message_count())?;
        dict.set_item("assistant_messages", self.assistant_message_count())?;
        
        // Cost metrics
        dict.set_item("total_cost", self.total_cost)?;
        dict.set_item("average_message_cost", 
            if self.messages.is_empty() { 0.0 } else { self.total_cost / self.messages.len() as f64 })?;
        
        // Tool metrics
        dict.set_item("unique_tools_used", self.tools_used.len())?;
        dict.set_item("total_tool_calls", self.inner.metadata.total_tool_calls)?;
        
        // Token metrics
        dict.set_item("total_input_tokens", self.inner.metadata.total_input_tokens)?;
        dict.set_item("total_output_tokens", self.inner.metadata.total_output_tokens)?;
        dict.set_item("total_tokens", 
            self.inner.metadata.total_input_tokens + self.inner.metadata.total_output_tokens)?;
        
        // Conversation metrics
        dict.set_item("conversation_depth", self.conversation_tree.stats.max_depth)?;
        dict.set_item("conversation_branches", self.conversation_tree.stats.num_branches)?;
        dict.set_item("sidechain_messages", 
            self.messages.iter().filter(|m| m.is_sidechain).count())?;
        
        // Duration metrics
        if let Some(duration) = self.duration {
            dict.set_item("duration_seconds", duration)?;
            dict.set_item("messages_per_minute", 
                if duration > 0 { (self.messages.len() as f64 * 60.0) / duration as f64 } else { 0.0 })?;
        }
        
        Ok(dict.into())
    }
    
    /// Convert session to a dictionary.
    /// 
    /// Returns:
    ///     Dict[str, Any]: Dictionary representation of the session
    fn to_dict(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new_bound(py);
        
        dict.set_item("session_id", &self.session_id)?;
        dict.set_item("total_cost", self.total_cost)?;
        dict.set_item("tools_used", &self.tools_used)?;
        dict.set_item("duration", self.duration)?;
        
        // Convert messages to list of dicts
        let messages_list = pyo3::types::PyList::empty_bound(py);
        for msg in &self.messages {
            let msg_dict = pyo3::types::PyDict::new_bound(py);
            msg_dict.set_item("role", &msg.role)?;
            msg_dict.set_item("text", &msg.text)?;
            msg_dict.set_item("cost", msg.cost)?;
            msg_dict.set_item("tools", &msg.tools)?;
            msg_dict.set_item("timestamp", &msg.timestamp)?;
            msg_dict.set_item("uuid", &msg.uuid)?;
            msg_dict.set_item("parent_uuid", &msg.parent_uuid)?;
            msg_dict.set_item("is_sidechain", msg.is_sidechain)?;
            msg_dict.set_item("cwd", &msg.cwd)?;
            messages_list.append(msg_dict)?;
        }
        dict.set_item("messages", messages_list)?;
        
        // Add metadata info
        let metadata_dict = pyo3::types::PyDict::new_bound(py);
        metadata_dict.set_item("total_messages", self.inner.metadata.total_messages)?;
        metadata_dict.set_item("user_messages", self.inner.metadata.user_messages)?;
        metadata_dict.set_item("assistant_messages", self.inner.metadata.assistant_messages)?;
        metadata_dict.set_item("total_cost_usd", self.inner.metadata.total_cost_usd)?;
        metadata_dict.set_item("total_input_tokens", self.inner.metadata.total_input_tokens)?;
        metadata_dict.set_item("total_output_tokens", self.inner.metadata.total_output_tokens)?;
        metadata_dict.set_item("unique_tools_used", &self.inner.metadata.unique_tools_used)?;
        metadata_dict.set_item("total_tool_calls", self.inner.metadata.total_tool_calls)?;
        dict.set_item("metadata", metadata_dict)?;
        
        Ok(dict.into())
    }
    
    fn __repr__(&self) -> String {
        format!("<Session id='{}' messages={} cost=${:.4}>",
            self.session_id, self.messages.len(), self.total_cost)
    }
    
    fn __str__(&self) -> String {
        format!("Session {} with {} messages (${:.4})", 
            self.session_id, self.messages.len(), self.total_cost)
    }
    
    fn __len__(&self) -> usize {
        self.messages.len()
    }
    
    fn __iter__(slf: PyRef<'_, Self>) -> PyResult<Py<MessageIterator>> {
        let iter = MessageIterator {
            messages: slf.messages.clone(),
            index: 0,
        };
        Py::new(slf.py(), iter)
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
///     path: Project directory path as Path object
///     sessions: List of Session objects for this project
///     total_cost: Total cost across all sessions in USD
///     total_messages: Total number of messages across all sessions  
///     session_count: Number of sessions in the project
///     
/// Methods:
///     get_session(session_id): Get a session by its ID
///     filter_sessions(predicate): Filter sessions with a custom predicate
///     get_all_messages(): Get all messages from all sessions
///     get_sessions_by_date_range(start, end): Get sessions within a date range
///     get_most_expensive_sessions(n): Get the n most expensive sessions
///     calculate_daily_costs(): Get daily cost breakdown
///     to_dict(): Convert project to a dictionary
/// 
/// Example:
///     >>> project = load_project("apply-model")
///     >>> print(f"Project: {project.name}")
///     >>> print(f"Sessions: {project.session_count}")
///     >>> print(f"Total cost: ${project.total_cost:.4f}")
///     >>> 
///     >>> # Get expensive sessions
///     >>> expensive = project.get_most_expensive_sessions(5)
///     >>> for session in expensive:
///     ...     print(f"Session {session.session_id}: ${session.total_cost:.4f}")
///     >>> 
///     >>> # Calculate daily costs
///     >>> daily_costs = project.calculate_daily_costs()
///     >>> for date, cost in daily_costs.items():
///     ...     print(f"{date}: ${cost:.4f}")
#[pyclass(name = "Project", module = "claude_sdk")]
pub struct Project {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub path: PyObject,  // pathlib.Path object
    // Store sessions as PyObject to avoid Clone requirement
    sessions_py: Py<pyo3::types::PyList>,
    #[pyo3(get)]
    pub total_cost: f64,
    #[pyo3(get)]
    pub total_messages: usize,
    #[pyo3(get)]
    pub session_count: usize,
    // Keep inner Rust project for efficient operations
    inner: Option<crate::types::Project>,
}

#[pymethods]
impl Project {
    #[getter]
    fn sessions(&self, py: Python<'_>) -> PyObject {
        self.sessions_py.clone_ref(py).into()
    }
    
    /// Get a session by its ID.
    /// 
    /// Args:
    ///     session_id: The session ID to look for
    /// 
    /// Returns:
    ///     Optional[Session]: The session if found, None otherwise
    fn get_session(&self, py: Python<'_>, session_id: &str) -> PyResult<PyObject> {
        let sessions_list = self.sessions_py.bind(py);
        
        for item in sessions_list.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            if session.borrow().session_id == session_id {
                return Ok(item.into());
            }
        }
        
        Ok(py.None())
    }
    
    /// Filter sessions with a custom predicate function.
    /// 
    /// Args:
    ///     predicate: A callable that takes a Session and returns bool
    /// 
    /// Returns:
    ///     List[Session]: Sessions that match the predicate
    /// 
    /// Example:
    ///     >>> # Find sessions with more than 100 messages
    ///     >>> large_sessions = project.filter_sessions(lambda s: len(s.messages) > 100)
    fn filter_sessions(&self, py: Python<'_>, predicate: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        let filtered = pyo3::types::PyList::empty_bound(py);
        let sessions_list = self.sessions_py.bind(py);
        
        for item in sessions_list.iter() {
            let result = predicate.call1((item.clone(),))?;
            if result.is_truthy()? {
                filtered.append(item)?;
            }
        }
        
        Ok(filtered.into())
    }
    
    /// Get all messages from all sessions.
    /// 
    /// Returns:
    ///     List[Message]: All messages from all sessions in chronological order
    fn get_all_messages(&self, py: Python<'_>) -> PyResult<PyObject> {
        let all_messages = pyo3::types::PyList::empty_bound(py);
        let sessions_list = self.sessions_py.bind(py);
        
        // Collect all messages with timestamps
        let mut messages_with_time: Vec<(PyObject, String)> = Vec::new();
        
        for item in sessions_list.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            for msg in &session.borrow().messages {
                messages_with_time.push((
                    Py::new(py, msg.clone())?.into(),
                    msg.timestamp.clone()
                ));
            }
        }
        
        // Sort by timestamp
        messages_with_time.sort_by(|a, b| a.1.cmp(&b.1));
        
        // Add sorted messages to list
        for (msg, _) in messages_with_time {
            all_messages.append(msg)?;
        }
        
        Ok(all_messages.into())
    }
    
    /// Get sessions within a date range.
    /// 
    /// Args:
    ///     start: Start date (datetime object or ISO string)
    ///     end: End date (datetime object or ISO string)
    /// 
    /// Returns:
    ///     List[Session]: Sessions that overlap with the date range
    fn get_sessions_by_date_range(&self, py: Python<'_>, start: &Bound<'_, PyAny>, end: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        // Convert start and end to ISO strings for comparison
        let start_str = if let Ok(s) = start.extract::<String>() {
            s
        } else {
            // Assume it's a datetime object
            start.call_method0("isoformat")?.extract::<String>()?
        };
        
        let end_str = if let Ok(s) = end.extract::<String>() {
            s
        } else {
            // Assume it's a datetime object
            end.call_method0("isoformat")?.extract::<String>()?
        };
        
        let filtered = pyo3::types::PyList::empty_bound(py);
        let sessions_list = self.sessions_py.bind(py);
        
        for item in sessions_list.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            let session_ref = session.borrow();
            
            // Check if session overlaps with date range
            if let (Some(start_time), Some(end_time)) = (session_ref.start_time(py)?, session_ref.end_time(py)?) {
                if !start_time.is_none() && !end_time.is_none() {
                    let session_start = start_time.call_method0(py, "isoformat")?.extract::<String>(py)?;
                    let session_end = end_time.call_method0(py, "isoformat")?.extract::<String>(py)?;
                    
                    // Check if session overlaps with the range
                    if session_start <= end_str && session_end >= start_str {
                        filtered.append(item)?;
                    }
                }
            }
        }
        
        Ok(filtered.into())
    }
    
    /// Get the n most expensive sessions.
    /// 
    /// Args:
    ///     n: Number of sessions to return
    /// 
    /// Returns:
    ///     List[Session]: The n most expensive sessions, sorted by cost (descending)
    fn get_most_expensive_sessions(&self, py: Python<'_>, n: usize) -> PyResult<PyObject> {
        let sessions_list = self.sessions_py.bind(py);
        
        // Collect sessions with costs
        let mut sessions_with_cost: Vec<(PyObject, f64)> = Vec::new();
        
        for item in sessions_list.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            sessions_with_cost.push((item.into(), session.borrow().total_cost));
        }
        
        // Sort by cost descending
        sessions_with_cost.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        
        // Take top n
        let result = pyo3::types::PyList::empty_bound(py);
        for (session, _) in sessions_with_cost.into_iter().take(n) {
            result.append(session)?;
        }
        
        Ok(result.into())
    }
    
    /// Calculate daily costs across all sessions.
    /// 
    /// Returns:
    ///     Dict[str, float]: Dictionary mapping date strings (YYYY-MM-DD) to daily costs
    fn calculate_daily_costs(&self, py: Python<'_>) -> PyResult<PyObject> {
        let daily_costs: std::collections::HashMap<String, f64> = std::collections::HashMap::new();
        let mut daily_costs = daily_costs;
        
        let sessions_list = self.sessions_py.bind(py);
        
        for item in sessions_list.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            let session_ref = session.borrow();
            
            // Get session messages and aggregate costs by day
            for msg in &session_ref.messages {
                if let Some(cost) = msg.cost {
                    // Extract date from timestamp (YYYY-MM-DD)
                    let date = msg.timestamp.split('T').next().unwrap_or("unknown");
                    *daily_costs.entry(date.to_string()).or_insert(0.0) += cost;
                }
            }
        }
        
        // Convert to Python dict
        let dict = pyo3::types::PyDict::new_bound(py);
        for (date, cost) in daily_costs {
            dict.set_item(date, cost)?;
        }
        
        Ok(dict.into())
    }
    
    /// Convert project to a dictionary.
    /// 
    /// Returns:
    ///     Dict[str, Any]: Dictionary representation of the project
    fn to_dict(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new_bound(py);
        
        dict.set_item("name", &self.name)?;
        dict.set_item("path", self.path.bind(py).call_method0("__str__")?)?;
        dict.set_item("total_cost", self.total_cost)?;
        dict.set_item("total_messages", self.total_messages)?;
        dict.set_item("session_count", self.session_count)?;
        
        // Convert sessions to list of dicts
        let sessions_list = pyo3::types::PyList::empty_bound(py);
        let py_sessions = self.sessions_py.bind(py);
        
        for item in py_sessions.iter() {
            let session: Bound<'_, Session> = item.extract()?;
            let session_dict = session.call_method0("to_dict")?;
            sessions_list.append(session_dict)?;
        }
        dict.set_item("sessions", sessions_list)?;
        
        Ok(dict.into())
    }
    
    fn __repr__(&self) -> String {
        format!("<Project name='{}' path='{}' sessions={} cost=${:.4}>",
            self.name, 
            self.inner.as_ref().map(|p| p.project_path.to_string_lossy().to_string()).unwrap_or_else(|| "unknown".to_string()),
            self.session_count, 
            self.total_cost)
    }
    
    fn __str__(&self) -> String {
        format!("Project '{}' with {} sessions (${:.4})", 
            self.name, self.session_count, self.total_cost)
    }
    
    fn __len__(&self) -> usize {
        self.session_count
    }
    
    fn __iter__(&self, py: Python<'_>) -> PyResult<PyObject> {
        // Return an iterator over sessions
        self.sessions_py.bind(py).call_method0("__iter__")
    }
}

impl Project {
    pub fn new(py: Python<'_>, name: String, path: PathBuf, sessions: Vec<Session>, inner: Option<crate::types::Project>) -> PyResult<Self> {
        // Create pathlib.Path object
        let pathlib = py.import_bound("pathlib")?;
        let path_class = pathlib.getattr("Path")?;
        let path_obj = path_class.call1((path.to_string_lossy().to_string(),))?;
        
        // Calculate aggregate statistics
        let total_cost = sessions.iter().map(|s| s.total_cost).sum();
        let total_messages = sessions.iter().map(|s| s.messages.len()).sum();
        let session_count = sessions.len();
        
        // Create Python list of sessions
        let sessions_list = pyo3::types::PyList::empty_bound(py);
        for session in sessions {
            let session_obj = Py::new(py, session)?;
            sessions_list.append(session_obj)?;
        }
        
        Ok(Project {
            name,
            path: path_obj.into(),
            sessions_py: sessions_list.into(),
            total_cost,
            total_messages,
            session_count,
            inner,
        })
    }
    
    pub fn from_rust_project(py: Python<'_>, project: crate::types::Project) -> PyResult<Self> {
        // Convert Rust sessions to Python sessions
        let sessions: Vec<Session> = project.sessions.iter()
            .map(|s| Session::from_rust_session(s.clone()))
            .collect();
        
        let name = project.name.clone();
        let path = project.project_path.clone();
        
        Self::new(py, name, path, sessions, Some(project))
    }
}