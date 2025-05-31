use std::path::{Path, PathBuf};
use chrono::{DateTime, Utc, Duration};
use std::collections::HashMap;

use super::session::ParsedSession;
use crate::utils::path::{decode_project_path, extract_project_name};
use crate::parser::SessionParser;
use crate::error::ClaudeError;

/// Project model that aggregates Claude Code sessions within a project directory
#[derive(Debug)]
pub struct Project {
    /// Encoded directory name (e.g., "-Users-darin-Projects-apply-model")
    pub project_id: String,
    /// Decoded filesystem path (e.g., "/Users/darin/Projects/apply-model")
    pub project_path: PathBuf,
    /// Display name for the project (e.g., "apply-model")
    pub name: String,
    /// Sessions belonging to this project
    pub sessions: Vec<ParsedSession>,
}

impl Project {
    /// Total cost of all sessions in the project in USD
    pub fn total_cost(&self) -> f64 {
        self.sessions.iter()
            .map(|session| session.metadata.total_cost_usd)
            .sum()
    }
    
    /// Set of all tool names used across all sessions in the project
    pub fn tools_used(&self) -> Vec<String> {
        let mut tools: std::collections::HashSet<String> = std::collections::HashSet::new();
        for session in &self.sessions {
            for tool in &session.metadata.unique_tools_used {
                tools.insert(tool.clone());
            }
        }
        let mut result: Vec<String> = tools.into_iter().collect();
        result.sort();
        result
    }
    
    /// Number of sessions in the project
    pub fn total_sessions(&self) -> usize {
        self.sessions.len()
    }
    
    /// Timestamp of the earliest session in the project
    pub fn first_session_date(&self) -> Option<DateTime<Utc>> {
        self.sessions.iter()
            .filter_map(|s| s.metadata.first_message_timestamp)
            .min()
    }
    
    /// Timestamp of the most recent session in the project
    pub fn last_session_date(&self) -> Option<DateTime<Utc>> {
        self.sessions.iter()
            .filter_map(|s| s.metadata.last_message_timestamp)
            .max()
    }
    
    /// Total time span from first to last session in the project
    pub fn total_duration(&self) -> Option<Duration> {
        match (self.first_session_date(), self.last_session_date()) {
            (Some(first), Some(last)) => Some(last - first),
            _ => None,
        }
    }
    
    /// Aggregated tool usage count across all sessions
    pub fn tool_usage_count(&self) -> HashMap<String, usize> {
        let mut counts = HashMap::new();
        
        for session in &self.sessions {
            for tool in &session.metadata.unique_tools_used {
                *counts.entry(tool.clone()).or_insert(0) += session.metadata.total_tool_calls;
            }
        }
        
        counts
    }
    
    /// Create a Project from a Claude Code project directory
    pub fn from_directory(project_dir: &Path) -> Result<Self, ClaudeError> {
        if !project_dir.exists() {
            return Err(ClaudeError::ParseError(crate::error::ParseError::CorruptedFile {
                reason: format!("Project directory does not exist: {:?}", project_dir),
            }));
        }
        
        if !project_dir.is_dir() {
            return Err(ClaudeError::ParseError(crate::error::ParseError::CorruptedFile {
                reason: format!("Not a directory: {:?}", project_dir),
            }));
        }
        
        // Get encoded project ID from directory name
        let project_id = project_dir
            .file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| ClaudeError::ParseError(crate::error::ParseError::CorruptedFile {
                reason: "Invalid directory name".to_string(),
            }))?
            .to_string();
        
        // Decode to get the original project path
        let project_path = decode_project_path(&project_id);
        let name = extract_project_name(&project_path);
        
        // Create project without sessions first
        let mut project = Self {
            project_id,
            project_path,
            name,
            sessions: Vec::new(),
        };
        
        // Load sessions from directory
        project.load_sessions(project_dir)?;
        
        Ok(project)
    }
    
    /// Create a Project from an encoded project ID
    pub fn from_encoded_id(project_id: &str, projects_base_dir: &Path) -> Result<Self, ClaudeError> {
        let project_dir = projects_base_dir.join(project_id);
        Self::from_directory(&project_dir)
    }
    
    /// Load sessions from the project directory
    fn load_sessions(&mut self, project_dir: &Path) -> Result<(), ClaudeError> {
        let session_files = SessionParser::discover_sessions(project_dir)?;
        
        for file_path in session_files {
            let parser = SessionParser::new(&file_path);
            
            // Handle empty files gracefully at the project level
            match parser.parse() {
                Ok(session) => self.sessions.push(session),
                Err(ClaudeError::ParseError(crate::error::ParseError::EmptyFile)) => {
                    // Skip empty files silently
                    continue;
                }
                Err(e) => {
                    // Log other errors but continue processing
                    eprintln!("Warning: Failed to parse session file {:?}: {}", file_path, e);
                    continue;
                }
            }
        }
        
        Ok(())
    }
    
    /// Get total message count across all sessions
    pub fn total_messages(&self) -> usize {
        self.sessions.iter()
            .map(|s| s.metadata.total_messages)
            .sum()
    }
    
    /// Get sessions sorted by start time
    pub fn sessions_by_date(&self) -> Vec<&ParsedSession> {
        let mut sessions: Vec<&ParsedSession> = self.sessions.iter().collect();
        sessions.sort_by_key(|s| s.metadata.first_message_timestamp);
        sessions
    }
    
    /// Get sessions that used a specific tool
    pub fn sessions_with_tool(&self, tool_name: &str) -> Vec<&ParsedSession> {
        self.sessions.iter()
            .filter(|s| s.metadata.unique_tools_used.contains(&tool_name.to_string()))
            .collect()
    }
    
    /// Get cost breakdown by session
    pub fn cost_breakdown(&self) -> Vec<(String, f64)> {
        self.sessions.iter()
            .map(|s| (s.session_id.clone(), s.metadata.total_cost_usd))
            .collect()
    }
}