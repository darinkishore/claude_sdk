use std::path::PathBuf;
use std::collections::{HashSet, HashMap};
use chrono::{DateTime, Utc};

use super::message::MessageRecord;
use super::content::ContentBlock;

/// Metadata about a parsed session
#[derive(Debug, Clone)]
pub struct SessionMetadata {
    // Message counts
    pub total_messages: usize,
    pub user_messages: usize,
    pub assistant_messages: usize,
    
    // Cost tracking
    pub total_cost_usd: f64,
    
    // Token usage
    pub total_input_tokens: u32,
    pub total_output_tokens: u32,
    pub cache_creation_tokens: u32,
    pub cache_read_tokens: u32,
    
    // Tool usage
    pub unique_tools_used: Vec<String>,
    pub total_tool_calls: usize,
    pub tool_usage_count: std::collections::HashMap<String, usize>,
    
    // Session timing
    pub session_file_path: PathBuf,
    pub first_message_timestamp: Option<DateTime<Utc>>,
    pub last_message_timestamp: Option<DateTime<Utc>>,
    pub session_duration: Option<chrono::Duration>,
    
    // Performance metrics
    pub total_duration_ms: u64,
    pub average_response_time_ms: Option<f64>,
}

impl SessionMetadata {
    /// Create metadata from a collection of messages
    pub fn from_messages(messages: &[MessageRecord], file_path: PathBuf) -> Self {
        let total_messages = messages.len();
        let user_messages = messages.iter().filter(|m| m.is_user_message()).count();
        let assistant_messages = messages.iter().filter(|m| m.is_assistant_message()).count();
        
        let total_cost_usd = messages.iter()
            .map(|m| m.cost())
            .sum();
            
        // Token aggregations
        let mut total_input_tokens = 0u32;
        let mut total_output_tokens = 0u32;
        let mut cache_creation_tokens = 0u32;
        let mut cache_read_tokens = 0u32;
        
        // Performance tracking
        let mut total_duration_ms = 0u64;
        let mut response_times = Vec::new();
        
        // Tool tracking
        let mut unique_tools = HashSet::new();
        let mut tool_usage_count: HashMap<String, usize> = HashMap::new();
        let mut total_tool_calls = 0;
        
        // Sort messages by timestamp for accurate timing
        let mut sorted_messages = messages.to_vec();
        sorted_messages.sort_by_key(|m| m.timestamp);
        
        for message in &sorted_messages {
            // Aggregate token usage
            if let Some(usage) = &message.message.usage {
                total_input_tokens = total_input_tokens.saturating_add(usage.input_tokens);
                total_output_tokens = total_output_tokens.saturating_add(usage.output_tokens);
                if let Some(cache_creation) = usage.cache_creation_input_tokens {
                    cache_creation_tokens = cache_creation_tokens.saturating_add(cache_creation);
                }
                if let Some(cache_read) = usage.cache_read_input_tokens {
                    cache_read_tokens = cache_read_tokens.saturating_add(cache_read);
                }
            }
            
            // Aggregate processing time
            if let Some(duration) = message.duration_ms {
                total_duration_ms += duration;
                if message.is_assistant_message() {
                    response_times.push(duration);
                }
            }
            
            // Count tool usage
            for content in &message.message.content {
                if let ContentBlock::ToolUse { name, .. } = content {
                    unique_tools.insert(name.clone());
                    *tool_usage_count.entry(name.clone()).or_insert(0) += 1;
                    total_tool_calls += 1;
                }
            }
        }
        
        let first_message_timestamp = sorted_messages.first().map(|m| m.timestamp);
        let last_message_timestamp = sorted_messages.last().map(|m| m.timestamp);
        
        // Calculate session duration
        let session_duration = match (first_message_timestamp, last_message_timestamp) {
            (Some(first), Some(last)) => Some(last - first),
            _ => None,
        };
        
        // Calculate average response time
        let average_response_time_ms = if !response_times.is_empty() {
            Some(response_times.iter().sum::<u64>() as f64 / response_times.len() as f64)
        } else {
            None
        };
        
        let unique_tools_used: Vec<String> = unique_tools.into_iter().collect();
        
        Self {
            total_messages,
            user_messages,
            assistant_messages,
            total_cost_usd,
            total_input_tokens,
            total_output_tokens,
            cache_creation_tokens,
            cache_read_tokens,
            unique_tools_used,
            total_tool_calls,
            tool_usage_count,
            session_file_path: file_path,
            first_message_timestamp,
            last_message_timestamp,
            session_duration,
            total_duration_ms,
            average_response_time_ms,
        }
    }
}