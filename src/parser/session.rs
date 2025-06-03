use std::io::{BufRead, BufReader};
use std::fs::File;
use std::path::{Path, PathBuf};

use crate::types::{MessageRecord, SummaryRecord, ParsedSession, SessionMetadata};
use crate::conversation::ConversationTree;
use crate::error::{ParseError, ClaudeError};

/// Parser for Claude Code JSONL session files
pub struct SessionParser {
    file_path: PathBuf,
}

impl SessionParser {
    /// Create a new session parser for the given file
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self {
            file_path: path.into(),
        }
    }
    
    /// Parse the entire session file
    pub fn parse(&self) -> Result<ParsedSession, ClaudeError> {
        let file = File::open(&self.file_path)?;
        let reader = BufReader::new(file);
        
        let mut messages = Vec::new();
        let mut summaries = Vec::new();
        let mut session_id = None;
        
        for (line_num, line) in reader.lines().enumerate() {
            let line = line?;
            
            // Skip empty lines
            if line.trim().is_empty() {
                continue;
            }
            
            // Check record type first
            let json_value: serde_json::Value = match serde_json::from_str(&line) {
                Ok(v) => v,
                Err(e) => {
                    return Err(ClaudeError::ParseError(ParseError::InvalidJsonl {
                        line: line_num + 1,
                        message: format!("Invalid JSON: {}", e),
                    }));
                }
            };
            
            // Check the type field
            match json_value.get("type").and_then(|t| t.as_str()) {
                Some("summary") => {
                    match serde_json::from_value::<SummaryRecord>(json_value) {
                        Ok(summary) => summaries.push(summary),
                        Err(e) => {
                            return Err(ClaudeError::ParseError(ParseError::InvalidJsonl {
                                line: line_num + 1,
                                message: format!("Invalid summary record: {}", e),
                            }));
                        }
                    }
                }
                Some("user") | Some("assistant") => {
                    match serde_json::from_value::<MessageRecord>(json_value) {
                        Ok(message) => {
                            // Extract session ID from first message
                            if session_id.is_none() {
                                session_id = Some(message.session_id.clone());
                            }
                            messages.push(message);
                        }
                        Err(e) => {
                            return Err(ClaudeError::ParseError(ParseError::InvalidJsonl {
                                line: line_num + 1,
                                message: format!("Invalid message record: {}", e),
                            }));
                        }
                    }
                }
                Some(other) => {
                    // Unknown record type - skip it
                    tracing::warn!("Unknown record type '{}' at line {}, skipping", other, line_num + 1);
                }
                None => {
                    return Err(ClaudeError::ParseError(ParseError::InvalidJsonl {
                        line: line_num + 1,
                        message: "Missing 'type' field".to_string(),
                    }));
                }
            }
        }
        
        if messages.is_empty() {
            return Err(ClaudeError::ParseError(ParseError::EmptyFile));
        }
        
        let session_id = session_id.ok_or_else(|| {
            ClaudeError::ParseError(ParseError::MissingField {
                field: "session_id".to_string(),
            })
        })?;
        
        // Build conversation tree
        let conversation_tree = ConversationTree::from_messages(messages.clone())?;
        
        // Generate metadata
        let metadata = SessionMetadata::from_messages(&messages, self.file_path.clone());
        
        Ok(ParsedSession {
            session_id,
            messages,
            summaries,
            conversation_tree,
            metadata,
        })
    }
    
    /// Get an iterator over all message records in the file
    pub fn records_iter(&self) -> Result<impl Iterator<Item = Result<MessageRecord, ParseError>>, ClaudeError> {
        let file = File::open(&self.file_path)?;
        let reader = BufReader::new(file);
        
        Ok(reader.lines().enumerate().filter_map(|(line_num, line_result)| {
            match line_result {
                Ok(line) => {
                    if line.trim().is_empty() {
                        return None;
                    }
                    
                    match serde_json::from_str::<MessageRecord>(&line) {
                        Ok(message) => Some(Ok(message)),
                        Err(parse_err) => Some(Err(ParseError::InvalidJsonl {
                            line: line_num + 1,
                            message: parse_err.to_string(),
                        })),
                    }
                }
                Err(io_err) => Some(Err(ParseError::InvalidJsonl {
                    line: line_num + 1,
                    message: io_err.to_string(),
                })),
            }
        }))
    }
    
    /// Extract tool usage patterns from the session
    pub fn extract_tool_usage(&self) -> Result<Vec<crate::types::ToolExecution>, ClaudeError> {
        use std::collections::HashMap;
        use crate::types::{ContentBlock, ToolExecution, ToolResult};
        use std::time::Duration;
        
        let session = self.parse()?;
        let mut tool_executions = Vec::new();
        let mut pending_tools: HashMap<String, (String, serde_json::Value, chrono::DateTime<chrono::Utc>)> = HashMap::new();
        
        for message in &session.messages {
            for content in &message.message.content {
                match content {
                    ContentBlock::ToolUse { id, name, input } => {
                        pending_tools.insert(id.clone(), (name.clone(), input.clone(), message.timestamp));
                    }
                    ContentBlock::ToolResult { tool_use_id, content, is_error } => {
                        if let Some((tool_name, input, start_time)) = pending_tools.remove(tool_use_id) {
                            let duration = Duration::from_millis(
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
                            
                            tool_executions.push(ToolExecution::new(
                                tool_name,
                                input,
                                tool_result,
                                duration,
                                message.timestamp,
                            ));
                        }
                    }
                    _ => {}
                }
            }
        }
        
        Ok(tool_executions)
    }
    
    /// Discover session files in a directory
    pub fn discover_sessions(dir: &Path) -> Result<Vec<PathBuf>, ClaudeError> {
        use std::fs;
        
        let mut session_files = Vec::new();
        
        fn visit_dir(dir: &Path, session_files: &mut Vec<PathBuf>) -> Result<(), std::io::Error> {
            for entry in fs::read_dir(dir)? {
                let entry = entry?;
                let path = entry.path();
                
                if path.is_dir() {
                    visit_dir(&path, session_files)?;
                } else if let Some(extension) = path.extension() {
                    if extension == "jsonl" {
                        session_files.push(path);
                    }
                }
            }
            Ok(())
        }
        
        visit_dir(dir, &mut session_files)?;
        Ok(session_files)
    }
    
    /// Get basic session info without full parsing
    pub fn session_info(&self) -> Result<SessionInfo, ClaudeError> {
        let file = File::open(&self.file_path)?;
        let reader = BufReader::new(file);
        
        let mut first_message: Option<MessageRecord> = None;
        let mut last_message: Option<MessageRecord> = None;
        let mut message_count = 0;
        let mut session_id = None;
        
        for line in reader.lines() {
            let line = line?;
            if line.trim().is_empty() {
                continue;
            }
            
            if let Ok(message) = serde_json::from_str::<MessageRecord>(&line) {
                if first_message.is_none() {
                    first_message = Some(message.clone());
                    session_id = Some(message.session_id.clone());
                }
                last_message = Some(message);
                message_count += 1;
            }
        }
        
        let session_id = session_id.ok_or_else(|| {
            ClaudeError::ParseError(ParseError::EmptyFile)
        })?;
        
        Ok(SessionInfo {
            session_id,
            file_path: self.file_path.clone(),
            message_count,
            first_timestamp: first_message.map(|m| m.timestamp),
            last_timestamp: last_message.map(|m| m.timestamp),
        })
    }
}

/// Basic information about a session without full parsing
#[derive(Debug, Clone)]
pub struct SessionInfo {
    pub session_id: String,
    pub file_path: PathBuf,
    pub message_count: usize,
    pub first_timestamp: Option<chrono::DateTime<chrono::Utc>>,
    pub last_timestamp: Option<chrono::DateTime<chrono::Utc>>,
}