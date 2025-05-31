use pyo3::prelude::*;
use std::collections::HashMap;

/// Metadata about a parsed session
/// 
/// This class provides detailed statistics and metadata about a Claude Code session,
/// including token usage, timing information, and tool usage patterns.
/// 
/// Properties:
///     total_messages: Total number of messages in the session
///     user_messages: Number of user messages
///     assistant_messages: Number of assistant messages
///     total_cost_usd: Total cost in USD
///     total_input_tokens: Total input tokens used
///     total_output_tokens: Total output tokens generated
///     cache_creation_tokens: Tokens used for cache creation
///     cache_read_tokens: Tokens read from cache
///     unique_tools_used: List of unique tool names used
///     total_tool_calls: Total number of tool invocations
///     tool_usage_count: Dictionary mapping tool names to usage counts
///     session_file_path: Path to the session file
///     first_message_timestamp: Timestamp of the first message
///     last_message_timestamp: Timestamp of the last message
///     session_duration: Duration of the session in seconds
///     total_duration_ms: Total processing time in milliseconds
///     average_response_time_ms: Average assistant response time
#[pyclass(name = "SessionMetadata", module = "claude_sdk")]
#[derive(Clone)]
pub struct SessionMetadata {
    #[pyo3(get)]
    pub total_messages: usize,
    #[pyo3(get)]
    pub user_messages: usize,
    #[pyo3(get)]
    pub assistant_messages: usize,
    #[pyo3(get)]
    pub total_cost_usd: f64,
    #[pyo3(get)]
    pub total_input_tokens: u32,
    #[pyo3(get)]
    pub total_output_tokens: u32,
    #[pyo3(get)]
    pub cache_creation_tokens: u32,
    #[pyo3(get)]
    pub cache_read_tokens: u32,
    #[pyo3(get)]
    pub unique_tools_used: Vec<String>,
    #[pyo3(get)]
    pub total_tool_calls: usize,
    #[pyo3(get)]
    pub tool_usage_count: HashMap<String, usize>,
    #[pyo3(get)]
    pub session_file_path: String,
    #[pyo3(get)]
    pub first_message_timestamp: Option<String>,
    #[pyo3(get)]
    pub last_message_timestamp: Option<String>,
    #[pyo3(get)]
    pub session_duration: Option<i64>, // Duration in seconds
    #[pyo3(get)]
    pub total_duration_ms: u64,
    #[pyo3(get)]
    pub average_response_time_ms: Option<f64>,
}

#[pymethods]
impl SessionMetadata {
    fn __repr__(&self) -> String {
        format!("<SessionMetadata messages={} cost=${:.4} tools={}>", 
            self.total_messages, self.total_cost_usd, self.unique_tools_used.len())
    }
}

impl SessionMetadata {
    pub fn from_rust_metadata(metadata: &crate::types::SessionMetadata) -> Self {
        Self {
            total_messages: metadata.total_messages,
            user_messages: metadata.user_messages,
            assistant_messages: metadata.assistant_messages,
            total_cost_usd: metadata.total_cost_usd,
            total_input_tokens: metadata.total_input_tokens,
            total_output_tokens: metadata.total_output_tokens,
            cache_creation_tokens: metadata.cache_creation_tokens,
            cache_read_tokens: metadata.cache_read_tokens,
            unique_tools_used: metadata.unique_tools_used.clone(),
            total_tool_calls: metadata.total_tool_calls,
            tool_usage_count: metadata.tool_usage_count.clone(),
            session_file_path: metadata.session_file_path.to_string_lossy().to_string(),
            first_message_timestamp: metadata.first_message_timestamp.map(|t| t.to_rfc3339()),
            last_message_timestamp: metadata.last_message_timestamp.map(|t| t.to_rfc3339()),
            session_duration: metadata.session_duration.map(|d| d.num_seconds()),
            total_duration_ms: metadata.total_duration_ms,
            average_response_time_ms: metadata.average_response_time_ms,
        }
    }
}

/// Result from a tool execution
/// 
/// Contains the output and status information from a tool invocation.
/// 
/// Properties:
///     tool_use_id: Unique identifier for this tool use
///     content: Output content from the tool
///     stdout: Standard output if available
///     stderr: Standard error if available
///     interrupted: Whether the execution was interrupted
///     is_error: Whether the execution resulted in an error
#[pyclass(name = "ToolResult", module = "claude_sdk")]
#[derive(Clone)]
pub struct ToolResult {
    #[pyo3(get)]
    pub tool_use_id: String,
    #[pyo3(get)]
    pub content: String,
    #[pyo3(get)]
    pub stdout: Option<String>,
    #[pyo3(get)]
    pub stderr: Option<String>,
    #[pyo3(get)]
    pub interrupted: bool,
    #[pyo3(get)]
    pub is_error: bool,
}

#[pymethods]
impl ToolResult {
    /// Check if this tool execution was successful
    fn is_success(&self) -> bool {
        !self.is_error && !self.interrupted
    }
    
    /// Get the effective output content
    fn effective_content(&self) -> &str {
        if self.is_error && !self.stderr.as_ref().unwrap_or(&String::new()).is_empty() {
            self.stderr.as_ref().unwrap()
        } else if !self.stdout.as_ref().unwrap_or(&String::new()).is_empty() {
            self.stdout.as_ref().unwrap()
        } else {
            &self.content
        }
    }
    
    fn __repr__(&self) -> String {
        format!("<ToolResult id='{}' success={}>", self.tool_use_id, self.is_success())
    }
}

/// Represents a complete tool execution with timing
/// 
/// This class captures a complete tool invocation including input, output, and timing.
/// 
/// Properties:
///     tool_name: Name of the tool executed
///     input: Input parameters passed to the tool (as dict)
///     output: ToolResult object with execution results
///     duration_ms: Execution duration in milliseconds
///     timestamp: When the tool was executed
#[pyclass(name = "ToolExecution", module = "claude_sdk")]
#[derive(Clone)]
pub struct ToolExecution {
    #[pyo3(get)]
    pub tool_name: String,
    #[pyo3(get)]
    pub output: ToolResult,
    #[pyo3(get)]
    pub duration_ms: u64,
    #[pyo3(get)]
    pub timestamp: String,
    // Store input as PyObject to handle JSON conversion
    input_json: serde_json::Value,
}

#[pymethods]
impl ToolExecution {
    #[getter]
    fn input(&self, py: Python<'_>) -> PyResult<PyObject> {
        // Convert serde_json::Value to Python dict
        crate::python::utils::json_to_py(py, &self.input_json)
    }
    
    /// Check if this tool execution was successful
    fn is_success(&self) -> bool {
        self.output.is_success()
    }
    
    fn __repr__(&self) -> String {
        format!("<ToolExecution tool='{}' duration_ms={} success={}>", 
            self.tool_name, self.duration_ms, self.is_success())
    }
}

impl ToolExecution {
    pub fn from_rust_execution(exec: &crate::types::ToolExecution) -> Self {
        let output = ToolResult {
            tool_use_id: exec.output.tool_use_id.clone(),
            content: exec.output.content.clone(),
            stdout: exec.output.stdout.clone(),
            stderr: exec.output.stderr.clone(),
            interrupted: exec.output.interrupted,
            is_error: exec.output.is_error,
        };
        
        Self {
            tool_name: exec.tool_name.clone(),
            output,
            duration_ms: exec.duration_ms(),
            timestamp: exec.timestamp.to_rfc3339(),
            input_json: exec.input.clone(),
        }
    }
}

/// Statistics about a conversation tree
/// 
/// Provides metrics about the structure of a conversation.
/// 
/// Properties:
///     total_messages: Total number of messages
///     max_depth: Maximum depth of the conversation tree
///     num_branches: Number of branching points
///     leaf_count: Number of leaf nodes (messages with no replies)
#[pyclass(name = "ConversationStats", module = "claude_sdk")]
#[derive(Clone)]
pub struct ConversationStats {
    #[pyo3(get)]
    pub total_messages: usize,
    #[pyo3(get)]
    pub max_depth: usize,
    #[pyo3(get)]
    pub num_branches: usize,
    #[pyo3(get)]
    pub leaf_count: usize,
}

#[pymethods]
impl ConversationStats {
    fn __repr__(&self) -> String {
        format!("<ConversationStats messages={} depth={} branches={}>", 
            self.total_messages, self.max_depth, self.num_branches)
    }
}

/// A node in the conversation tree
/// 
/// Represents a single message and its children in the conversation tree structure.
/// 
/// Properties:
///     message: The Message object at this node
///     children: List of child ConversationNode objects
#[pyclass(name = "ConversationNode", module = "claude_sdk")]
pub struct ConversationNode {
    #[pyo3(get)]
    pub message: crate::python::classes::Message,
    children_nodes: Vec<Box<ConversationNode>>,
}

#[pymethods]
impl ConversationNode {
    #[getter]
    fn children(&self) -> Vec<ConversationNode> {
        self.children_nodes.iter()
            .map(|child| (**child).clone())
            .collect()
    }
    
    /// Check if this node is a leaf (has no children)
    fn is_leaf(&self) -> bool {
        self.children_nodes.is_empty()
    }
    
    /// Get the number of children
    fn child_count(&self) -> usize {
        self.children_nodes.len()
    }
    
    fn __repr__(&self) -> String {
        format!("<ConversationNode uuid='{}' children={}>", 
            self.message.uuid, self.child_count())
    }
}

impl Clone for ConversationNode {
    fn clone(&self) -> Self {
        Self {
            message: self.message.clone(),
            children_nodes: self.children_nodes.clone(),
        }
    }
}

impl ConversationNode {
    pub fn from_rust_node(node: &crate::conversation::ConversationNode) -> Self {
        let message = crate::python::classes::Message::from_rust_message(&node.message);
        let children_nodes = node.children.iter()
            .map(|child| Box::new(Self::from_rust_node(child)))
            .collect();
        
        Self {
            message,
            children_nodes,
        }
    }
}

/// Represents a conversation as a tree structure
/// 
/// This class provides a tree representation of the conversation, showing how messages
/// branch and reply to each other. It's useful for analyzing conversation flow and
/// finding sidechains or branches.
/// 
/// Properties:
///     root_messages: List of root ConversationNode objects (messages with no parent)
///     orphaned_messages: List of message UUIDs with missing parents
///     circular_references: List of (uuid, uuid) tuples indicating circular references
///     stats: ConversationStats object with tree metrics
#[pyclass(name = "ConversationTree", module = "claude_sdk")]
#[derive(Clone)]
pub struct ConversationTree {
    root_nodes: Vec<ConversationNode>,
    #[pyo3(get)]
    pub orphaned_messages: Vec<String>,
    #[pyo3(get)]
    pub circular_references: Vec<(String, String)>,
    #[pyo3(get)]
    pub stats: ConversationStats,
}

#[pymethods]
impl ConversationTree {
    #[getter]
    fn root_messages(&self) -> Vec<ConversationNode> {
        self.root_nodes.clone()
    }
    
    /// Get the maximum depth of the conversation tree
    fn max_depth(&self) -> usize {
        self.stats.max_depth
    }
    
    /// Count the number of branching points
    fn count_branches(&self) -> usize {
        self.stats.num_branches
    }
    
    fn __repr__(&self) -> String {
        format!("<ConversationTree roots={} messages={} depth={}>", 
            self.root_nodes.len(), self.stats.total_messages, self.stats.max_depth)
    }
}

impl ConversationTree {
    pub fn from_rust_tree(tree: &crate::conversation::ConversationTree) -> Self {
        let root_nodes = tree.root_messages.iter()
            .map(ConversationNode::from_rust_node)
            .collect();
        
        let orphaned_messages = tree.orphaned_messages.iter()
            .map(|uuid| uuid.to_string())
            .collect();
        
        let circular_references = tree.circular_references.iter()
            .map(|(a, b)| (a.to_string(), b.to_string()))
            .collect();
        
        let stats = ConversationStats {
            total_messages: tree.stats().total_messages,
            max_depth: tree.stats().max_depth,
            num_branches: tree.stats().num_branches,
            leaf_count: tree.stats().leaf_count,
        };
        
        Self {
            root_nodes,
            orphaned_messages,
            circular_references,
            stats,
        }
    }
}

/// A block of text content in a message
#[pyclass(name = "TextBlock", module = "claude_sdk")]
#[derive(Clone)]
pub struct TextBlock {
    #[pyo3(get)]
    pub text: String,
}

#[pymethods]
impl TextBlock {
    fn __repr__(&self) -> String {
        let preview = if self.text.len() > 50 {
            format!("{}...", &self.text[..50])
        } else {
            self.text.clone()
        };
        format!("<TextBlock text='{}'>", preview)
    }
}

/// A tool use block in a message
/// 
/// Represents a tool invocation within a message, including the tool name,
/// input parameters, and invocation ID.
/// 
/// Properties:
///     id: Unique identifier for this tool use
///     name: Name of the tool being invoked
///     input: Input parameters as a dictionary
#[pyclass(name = "ToolUseBlock", module = "claude_sdk")]
#[derive(Clone)]
pub struct ToolUseBlock {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub name: String,
    input_json: serde_json::Value,
}

#[pymethods]
impl ToolUseBlock {
    #[getter]
    fn input(&self, py: Python<'_>) -> PyResult<PyObject> {
        // Convert serde_json::Value to Python dict
        crate::python::utils::json_to_py(py, &self.input_json)
    }
    
    fn __repr__(&self) -> String {
        format!("<ToolUseBlock id='{}' name='{}'>", self.id, self.name)
    }
}

impl ToolUseBlock {
    pub fn from_content_block(id: String, name: String, input: serde_json::Value) -> Self {
        Self {
            id,
            name,
            input_json: input,
        }
    }
}