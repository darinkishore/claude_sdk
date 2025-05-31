use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::message::MessageRecord;
use super::enums::OutputFormat;
use super::metadata::SessionMetadata;
use crate::conversation::ConversationTree;

/// Type alias for session identifiers
pub type SessionId = String;

/// Configuration for a Claude session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionConfig {
    pub model: String,
    pub max_turns: Option<u32>,
    pub output_format: OutputFormat,
    pub allowed_tools: Vec<String>,
    pub disallowed_tools: Vec<String>, 
    pub system_prompt: Option<String>,
    pub append_system_prompt: Option<String>,
}


/// Summary record for compacted sessions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SummaryRecord {
    #[serde(rename = "type")]
    pub record_type: String, // "summary"
    pub summary: String,
    #[serde(rename = "leafUuid")]
    pub leaf_uuid: Uuid,
}

/// Parsed session data with metadata
#[derive(Debug)]
pub struct ParsedSession {
    pub session_id: SessionId,
    pub messages: Vec<MessageRecord>,
    pub summaries: Vec<SummaryRecord>,
    pub conversation_tree: ConversationTree,
    pub metadata: SessionMetadata,
}


impl ParsedSession {
    /// Get total cost for this session
    pub fn total_cost(&self) -> f64 {
        self.metadata.total_cost_usd
    }
    
    /// Get total duration for this session
    pub fn total_duration_ms(&self) -> u64 {
        self.metadata.total_duration_ms
    }
    
    /// Get all user messages
    pub fn user_messages(&self) -> Vec<&MessageRecord> {
        self.messages.iter()
            .filter(|msg| msg.is_user_message())
            .collect()
    }
    
    /// Get all assistant messages
    pub fn assistant_messages(&self) -> Vec<&MessageRecord> {
        self.messages.iter()
            .filter(|msg| msg.is_assistant_message())
            .collect()
    }
    
    /// Get messages within a time range
    pub fn messages_in_range(
        &self, 
        start: chrono::DateTime<chrono::Utc>, 
        end: chrono::DateTime<chrono::Utc>
    ) -> Vec<&MessageRecord> {
        self.messages.iter()
            .filter(|msg| msg.timestamp >= start && msg.timestamp <= end)
            .collect()
    }
}