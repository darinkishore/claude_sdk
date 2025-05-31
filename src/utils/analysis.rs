/// Utility functions for the Claude Code SDK

use std::collections::HashMap;
use crate::types::{MessageRecord, ToolExecution};

/// Analyze patterns in tool usage
pub fn analyze_tool_patterns(executions: &[ToolExecution]) -> Vec<ToolPattern> {
    let mut patterns = HashMap::new();
    
    for execution in executions {
        let pattern = patterns
            .entry(execution.tool_name.clone())
            .or_insert_with(|| ToolPattern {
                tool_name: execution.tool_name.clone(),
                frequency: 0,
                success_rate: 0.0,
                avg_duration_ms: 0.0,
                total_executions: 0,
                successful_executions: 0,
            });
        
        pattern.total_executions += 1;
        if execution.is_success() {
            pattern.successful_executions += 1;
        }
    }
    
    // Calculate rates and averages
    for pattern in patterns.values_mut() {
        pattern.frequency = pattern.total_executions;
        pattern.success_rate = if pattern.total_executions > 0 {
            pattern.successful_executions as f64 / pattern.total_executions as f64
        } else {
            0.0
        };
        
        let total_duration: u64 = executions
            .iter()
            .filter(|e| e.tool_name == pattern.tool_name)
            .map(|e| e.duration_ms())
            .sum();
            
        pattern.avg_duration_ms = if pattern.total_executions > 0 {
            total_duration as f64 / pattern.total_executions as f64
        } else {
            0.0
        };
    }
    
    let mut result: Vec<_> = patterns.into_values().collect();
    result.sort_by(|a, b| b.frequency.cmp(&a.frequency));
    result
}

/// Represents a pattern in tool usage
#[derive(Debug, Clone)]
pub struct ToolPattern {
    pub tool_name: String,
    pub frequency: usize,
    pub success_rate: f64,
    pub avg_duration_ms: f64,
    pub total_executions: usize,
    pub successful_executions: usize,
}

/// Calculate basic performance metrics for a session
pub fn calculate_session_metrics(messages: &[MessageRecord]) -> SessionMetrics {
    let total_messages = messages.len();
    let total_cost = messages.iter().map(|m| m.cost()).sum();
    let total_duration_ms = messages.iter().map(|m| m.duration()).sum();
    
    let user_messages = messages.iter().filter(|m| m.is_user_message()).count();
    let assistant_messages = messages.iter().filter(|m| m.is_assistant_message()).count();
    
    let avg_cost_per_message = if total_messages > 0 {
        total_cost / total_messages as f64
    } else {
        0.0
    };
    
    let avg_duration_per_message = if total_messages > 0 {
        total_duration_ms as f64 / total_messages as f64
    } else {
        0.0
    };
    
    SessionMetrics {
        total_messages,
        user_messages,
        assistant_messages,
        total_cost,
        total_duration_ms,
        avg_cost_per_message,
        avg_duration_per_message,
    }
}

/// Basic performance metrics for a session
#[derive(Debug, Clone)]
pub struct SessionMetrics {
    pub total_messages: usize,
    pub user_messages: usize,
    pub assistant_messages: usize,
    pub total_cost: f64,
    pub total_duration_ms: u64,
    pub avg_cost_per_message: f64,
    pub avg_duration_per_message: f64,
}