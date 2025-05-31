# 🦀 Rust Claude Code SDK: Technical Specification

**Version**: 0.1.0-draft  
**Status**: Design Phase  
**Priority**: T0 - Observability Foundation  

---

## **Overview**

A composable, low-level Rust library providing rich abstractions over Claude Code's data model and execution capabilities. Designed for building observability systems, pattern recognition, and downstream optimization tools (DSPy integration, workflow automation, etc.).

### **Core Principles**
- **Data Access First**: Clean, efficient access to Claude Code's data structures
- **Zero-Copy Efficiency**: Leverage Rust's ownership system for performance
- **Minimal Abstractions**: Provide data types and parsers, not opinions
- **Type Safety**: Prevent data corruption through strong typing
- **Python-Bindable**: Clean FFI for downstream Python tooling

---

## **Implementation Phases**

### **T0: Data Access Foundation** 🎯
**Goal**: Rich data model, session parsing, data extraction
- [ ] Claude Code JSONL format parsing
- [ ] Message threading and conversation reconstruction  
- [ ] Tool usage extraction
- [ ] Performance metrics access (cost, timing, token usage)
- [ ] Raw data structures with zero interpretation

### **T1: Execution Engine**
**Goal**: Programmatic Claude Code execution and session management
- [ ] Claude binary integration (`--output-format json`)
- [ ] Session configuration and management
- [ ] Interactive vs non-interactive mode support
- [ ] Real-time trace streaming
- [ ] Error handling and recovery

### **T2: Git Integration** ⚠️ **RESEARCH NEEDED**
**Goal**: Correlate AI interactions with actual code changes
- [ ] Research: `git2` vs `gitoxide` vs other Rust git libraries
- [ ] Git state capture (before/after execution)
- [ ] Diff analysis and file change tracking
- [ ] Commit correlation with session outcomes
- [ ] Branch/merge workflow awareness

### **T3: MCP Support** ⚠️ **LOWEST PRIORITY**
**Goal**: Model Context Protocol server integration
- [ ] MCP server configuration (JSON + idiomatic Rust config)
- [ ] Runtime MCP server management
- [ ] Tool permission handling
- [ ] Compile-time MCP validation (possibly with Nix devshell)
- [ ] Standard stdio MCP support

---

## **Data Model Architecture**

### **Core Types**

```rust
// === Session Management ===
#[derive(Debug, Clone)]
pub struct ClaudeSession {
    pub id: SessionId,
    pub config: SessionConfig,
    pub directory: PathBuf,
    pub git_context: Option<GitContext>, // T2
    trace_stream: TraceStream,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionConfig {
    pub model: String,                    // "claude-sonnet-4"
    pub max_turns: Option<u32>,
    pub output_format: OutputFormat,      // Text, Json, StreamJson
    pub allowed_tools: Vec<String>,
    pub disallowed_tools: Vec<String>, 
    pub system_prompt: Option<String>,
    pub append_system_prompt: Option<String>,
    pub mcp_config: Option<PathBuf>,      // T3
    pub permission_prompt_tool: Option<String>, // T3
}

// === Message Types (Direct mapping to Claude Code JSONL) ===
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageRecord {
    pub parent_uuid: Option<Uuid>,
    pub is_sidechain: bool,
    pub user_type: UserType,
    pub cwd: PathBuf,
    pub session_id: SessionId,
    pub version: String,
    pub message_type: MessageType, // "user" | "assistant"
    pub message: Message,
    pub cost_usd: Option<f64>,
    pub duration_ms: Option<u64>,
    pub request_id: Option<String>,
    pub uuid: Uuid,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Option<String>,
    pub role: Role, // User, Assistant
    pub model: Option<String>,
    pub content: Vec<ContentBlock>,
    pub stop_reason: Option<StopReason>,
    pub usage: Option<TokenUsage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ContentBlock {
    Text { 
        text: String 
    },
    Thinking { 
        thinking: String, 
        signature: String 
    },
    ToolUse { 
        id: String, 
        name: String, 
        input: serde_json::Value 
    },
}

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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    pub input_tokens: u32,
    pub cache_creation_input_tokens: u32,
    pub cache_read_input_tokens: u32,
    pub output_tokens: u32,
    pub service_tier: String,
}

// === Summary Records (Compacted Sessions) ===
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SummaryRecord {
    pub record_type: String, // "summary"
    pub summary: String,
    pub leaf_uuid: Uuid,
}
```

### **Execution Types**

```rust
// === Execution Results ===
#[derive(Debug, Clone)]
pub struct ExecutionResult {
    pub session_id: SessionId,
    pub claude_output: ClaudeOutput,
    pub git_before: Option<GitState>, // T2
    pub git_after: Option<GitState>,  // T2
    pub duration: Duration,
    pub cost_usd: f64,
    pub exit_success: bool, // Did claude command succeed
}

// === Raw Tool Data ===
#[derive(Debug, Clone)]
pub struct ToolExecution {
    pub tool_name: String,
    pub input: serde_json::Value,
    pub output: ToolResult,
    pub duration: Duration,
    pub timestamp: DateTime<Utc>,
}
```

---

## **Core Abstractions**

### **1. Session Builder (Composable Configuration)**

```rust
pub struct ClaudeSessionBuilder {
    directory: PathBuf,
    config: SessionConfig,
}

impl ClaudeSessionBuilder {
    pub fn new(directory: impl Into<PathBuf>) -> Self
    pub fn with_model(self, model: &str) -> Self
    pub fn with_max_turns(self, turns: u32) -> Self
    pub fn with_system_prompt(self, prompt: &str) -> Self
    pub fn with_git_tracking(self) -> Self              // T2
    pub fn with_mcp_config(self, config: PathBuf) -> Self // T3
    pub fn build(self) -> Result<ClaudeSession, ClaudeError>
}
```

### **2. Data Processing (Sync File Access)**

```rust
use std::fs::File;
use std::io::{BufWriter, BufReader};

pub struct TraceWriter {
    session_file: Option<BufWriter<File>>,
}

impl TraceWriter {
    pub fn record(&mut self, record: MessageRecord) -> Result<(), TraceError>
    pub fn records_iter(&self) -> impl Iterator<Item = Result<MessageRecord, TraceError>>
}
```

### **3. Session Parser (JSONL Processing)**

```rust
use std::io::BufReader;

pub struct SessionParser {
    file_path: PathBuf,
}

impl SessionParser {
    pub fn new(path: impl Into<PathBuf>) -> Self
    pub fn parse(&self) -> Result<ParsedSession, ParseError>
    pub fn records_iter(&self) -> impl Iterator<Item = Result<MessageRecord, ParseError>>
    pub fn get_conversation_tree(&self) -> Result<ConversationTree, ParseError>
    pub fn extract_tool_usage(&self) -> Result<Vec<ToolExecution>, ParseError>
}

#[derive(Debug)]
pub struct ParsedSession {
    pub session_id: SessionId,
    pub messages: Vec<MessageRecord>,
    pub summaries: Vec<SummaryRecord>,
    pub conversation_tree: ConversationTree,
    pub metadata: SessionMetadata,
}

#[derive(Debug)]
pub struct ConversationTree {
    pub root_messages: Vec<ConversationNode>,
}

#[derive(Debug)]
pub struct ConversationNode {
    pub message: MessageRecord,
    pub children: Vec<ConversationNode>,
}
```

### **4. Claude Executor (Process Management)**

```rust
use std::process::Command;
use crossbeam::thread;

pub struct ClaudeExecutor {
    config: SessionConfig,
    claude_binary: PathBuf,
}

impl ClaudeExecutor {
    pub fn new(claude_binary: impl Into<PathBuf>) -> Self
    pub fn with_config(mut self, config: SessionConfig) -> Self
    
    pub fn execute_prompt(
        &self,
        prompt: &str,
        session_id: Option<SessionId>,
    ) -> Result<ClaudeOutput, ExecutionError>
    
    pub fn start_interactive_session(
        &self,
        directory: PathBuf,
    ) -> Result<InteractiveSession, ExecutionError>
    
    pub fn resume_session(
        &self,
        session_id: SessionId,
    ) -> Result<ClaudeOutput, ExecutionError>
    
    pub fn continue_latest_session(&self) -> Result<ClaudeOutput, ExecutionError>
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudeOutput {
    pub role: String,
    pub cost_usd: f64,
    pub duration_ms: u64,
    pub duration_api_ms: u64,
    pub result: String,
    pub session_id: SessionId,
}
```

---

## **Error Handling**

```rust
#[derive(Debug, thiserror::Error)]
pub enum ClaudeError {
    #[error("Session not found: {session_id}")]
    SessionNotFound { session_id: SessionId },
    
    #[error("Parse error: {0}")]
    ParseError(#[from] ParseError),
    
    #[error("Execution error: {0}")]
    ExecutionError(#[from] ExecutionError),
    
    #[error("Git error: {0}")]
    GitError(#[from] GitError), // T2
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::Error),
}

#[derive(Debug, thiserror::Error)]
pub enum ExecutionError {
    #[error("Claude binary not found at: {path}")]
    ClaudeBinaryNotFound { path: PathBuf },
    
    #[error("Claude execution failed: {stderr}")]
    ClaudeFailure { stderr: String, exit_code: Option<i32> },
    
    #[error("Invalid output format: {0}")]
    InvalidOutput(String),
    
    #[error("Timeout after {duration:?}")]
    Timeout { duration: Duration },
}
```

---

## **Usage Examples**

### **Basic Session Analysis**
```rust
use claude_code_sdk::*;

fn main() -> Result<(), ClaudeError> {
    // Parse existing session
    let parser = SessionParser::new("~/.claude/projects/my-project/session.jsonl");
    let session = parser.parse()?;
    
    println!("Session: {}", session.session_id);
    println!("Total messages: {}", session.messages.len());
    println!("Total cost: ${:.4}", session.total_cost());
    
    // Extract patterns using iterator
    let patterns = parser.analyze_patterns()?;
    for pattern in patterns {
        println!("Pattern: {:?}, Frequency: {}", pattern.pattern_type, pattern.frequency);
    }
    
    Ok(())
}
```

### **Live Session Execution**
```rust
use std::thread;

fn main() -> Result<(), ClaudeError> {
    // Create session 
    let mut session = ClaudeSessionBuilder::new("/path/to/project")
        .with_model("claude-sonnet-4")
        .build()?;
    
    // Execute and capture raw data
    let result = session.execute("Fix the authentication bug")?;
    
    println!("Cost: ${:.4}", result.cost_usd);
    println!("Success: {}", result.exit_success);
    
    // Access raw tool usage
    let tools = result.extract_tool_usage();
    println!("Tools used: {:?}", tools.iter().map(|t| &t.tool_name).collect::<Vec<_>>());
    
    Ok(())
}
```

### **Batch Data Access**
```rust
use claude_code_sdk::*;
use crossbeam::thread;
use std::path::Path;

fn main() -> Result<(), ClaudeError> {
    // Access all sessions in directory
    let claude_dir = Path::new("~/.claude/projects");
    let sessions = SessionParser::discover_sessions(claude_dir)?;
    
    // Process sessions in parallel using crossbeam
    let results: Vec<_> = thread::scope(|s| {
        sessions.into_iter().map(|session_path| {
            s.spawn(move |_| {
                let parser = SessionParser::new(session_path);
                parser.parse()
            })
        }).collect::<Vec<_>>().into_iter().map(|h| h.join().unwrap()).collect()
    });
    
    let total_cost: f64 = results.iter().filter_map(|r| r.as_ref().ok()).map(|s| s.total_cost()).sum();
    let total_messages: usize = results.iter().filter_map(|r| r.as_ref().ok()).map(|s| s.messages.len()).sum();
    
    println!("Total sessions: {}", results.len());
    println!("Total cost: ${:.2}", total_cost);
    println!("Total messages: {}", total_messages);
    
    Ok(())
}
```

---

## **Research & Uncertainties**

### **🔍 Git Library Research (T2)**
**Status**: Research required
**Options**:
- `git2` - Mature, widely used, libgit2 bindings
- `gitoxide` - Pure Rust, modern, potentially faster
- `git-rs` - Alternative pure Rust implementation

**Evaluation Criteria**:
- Performance for large repositories
- API ergonomics for our use cases
- Async support
- Repository state capture efficiency
- Diff generation capabilities

### **🔍 MCP Configuration Design (T3)**
**Status**: Design exploration needed
**Questions**:
- JSON-only vs idiomatic Rust config (TOML/RON)?
- Compile-time validation approach?
- Runtime MCP server lifecycle management?
- Integration with Nix devshell for development?

### **🔍 Session File Watching**
**Status**: Implementation approach TBD
**Options**:
- `notify` crate for filesystem watching
- Polling vs event-driven updates
- Real-time vs batch processing
- Memory usage for large session files

### **🔍 Performance Considerations**
**Status**: Benchmarking needed
**Areas**:
- JSONL parsing performance for large files
- Memory usage for conversation tree reconstruction
- Async vs sync API trade-offs
- Zero-copy optimization opportunities

---

## **Dependencies (Sync-Based)**

```toml
[dependencies]
# Core parsing and data types
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
uuid = { version = "1.17", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
thiserror = "2.0"

# Threading and parallel processing
crossbeam = "0.8"

# Git (T2 - research needed)
# git2 = "0.18"              # Option 1
# gitoxide = "0.61"          # Option 2

# File watching (if needed)
# notify = "6.0"

# MCP support (T3)
# To be determined

[dev-dependencies]
tempfile = "3.20"
```

**Sync Design Benefits:**
- **Simpler Error Handling**: No async-specific error propagation
- **Standard Threading**: Use `std::thread` and `crossbeam` for parallelism
- **Zero Runtime Overhead**: No async runtime complexity
- **Easier Testing**: Standard Rust testing without async test frameworks
- **File I/O Simplicity**: `std::fs::File` and `BufReader` instead of async I/O

---

## **Success Criteria**

### **T0 Success Metrics**
- [ ] Parse any Claude Code JSONL session file without errors
- [ ] Reconstruct conversation threading perfectly
- [ ] Extract tool usage patterns with 100% accuracy
- [ ] Identify basic success/failure indicators
- [ ] Generate meaningful performance metrics
- [ ] Handle large session files (>1MB) efficiently

### **T1 Success Metrics**
- [ ] Execute Claude Code programmatically with all configuration options
- [ ] Capture execution results with rich metadata
- [ ] Support both interactive and non-interactive modes
- [ ] Handle all Claude Code error conditions gracefully
- [ ] Stream trace data in real-time

### **T2 Success Metrics** (Git Integration)
- [ ] Capture git state before/after Claude execution
- [ ] Correlate file changes with AI interactions
- [ ] Generate meaningful diff analysis
- [ ] Support complex git workflows (branches, merges)

### **T3 Success Metrics** (MCP)
- [ ] Configure MCP servers idomatically
- [ ] Validate MCP configuration at compile time
- [ ] Manage MCP server lifecycle
- [ ] Handle MCP tool permissions properly

---

## **Next Steps**

1. **Create Rust project structure**
2. **Implement T0: Basic JSONL parsing and data model**
3. **Add comprehensive tests with real Claude Code session data**
4. **Research git library options (T2)**
5. **Implement T1: Claude execution engine**
6. **Design MCP integration approach (T3)**

---

*This specification serves as the foundational design document for the Rust Claude Code SDK. It prioritizes observability and composability while acknowledging areas requiring further research and design exploration.*