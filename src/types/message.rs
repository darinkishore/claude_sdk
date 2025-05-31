use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use std::path::PathBuf;

use super::content::{ContentBlock, deserialize_message_content};
use super::enums::{UserType, MessageType, Role, StopReason};

/// Represents a single message record from Claude Code JSONL
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageRecord {
    #[serde(rename = "parentUuid")]
    pub parent_uuid: Option<Uuid>,
    #[serde(rename = "isSidechain")]
    pub is_sidechain: bool,
    #[serde(rename = "userType")]
    pub user_type: UserType,
    pub cwd: PathBuf,
    #[serde(rename = "sessionId")]
    pub session_id: String,
    pub version: String,
    #[serde(rename = "type")]
    pub message_type: MessageType,
    pub message: Message,
    #[serde(rename = "costUSD")]
    pub cost_usd: Option<f64>,
    #[serde(rename = "durationMs")]
    pub duration_ms: Option<u64>,
    #[serde(rename = "requestId")]
    pub request_id: Option<String>,
    pub uuid: Uuid,
    pub timestamp: DateTime<Utc>,
    #[serde(rename = "toolUseResult")]
    pub tool_use_result: Option<serde_json::Value>,
    #[serde(rename = "isMeta")]
    pub is_meta: Option<bool>,
}


/// Core message structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Option<String>,
    pub role: Role,
    pub model: Option<String>,
    #[serde(default, deserialize_with = "deserialize_message_content")]
    pub content: Vec<ContentBlock>,
    #[serde(rename = "stop_reason")]
    pub stop_reason: Option<StopReason>,
    pub usage: Option<TokenUsage>,
}




/// Token usage statistics for a message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    #[serde(rename = "input_tokens")]
    pub input_tokens: u32,
    #[serde(rename = "cache_creation_input_tokens")]
    pub cache_creation_input_tokens: Option<u32>,
    #[serde(rename = "cache_read_input_tokens")]
    pub cache_read_input_tokens: Option<u32>,
    #[serde(rename = "output_tokens")]
    pub output_tokens: u32,
    #[serde(rename = "service_tier")]
    pub service_tier: Option<String>,
}

impl MessageRecord {
    /// Check if this message is from a human user
    pub fn is_user_message(&self) -> bool {
        matches!(self.message_type, MessageType::User)
    }
    
    /// Check if this message is from the assistant
    pub fn is_assistant_message(&self) -> bool {
        matches!(self.message_type, MessageType::Assistant)
    }
    
    /// Get the total cost of this message
    pub fn cost(&self) -> f64 {
        self.cost_usd.unwrap_or(0.0)
    }
    
    /// Get the duration of this message in milliseconds
    pub fn duration(&self) -> u64 {
        self.duration_ms.unwrap_or(0)
    }
    
    /// Extract tool uses from this message
    pub fn tool_uses(&self) -> Vec<&ContentBlock> {
        self.message.content.iter()
            .filter(|block| matches!(block, ContentBlock::ToolUse { .. }))
            .collect()
    }
    
    /// Extract tool results from this message
    pub fn tool_results(&self) -> Vec<&ContentBlock> {
        self.message.content.iter()
            .filter(|block| matches!(block, ContentBlock::ToolResult { .. }))
            .collect()
    }
    
    /// Extract all text content from this message
    pub fn text_content(&self) -> String {
        self.message.content.iter()
            .filter_map(|block| match block {
                ContentBlock::Text { text } => Some(text.as_str()),
                ContentBlock::Thinking { thinking, .. } => Some(thinking.as_str()),
                _ => None,
            })
            .collect::<Vec<_>>()
            .join("\n")
    }
}