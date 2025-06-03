use std::path::PathBuf;
use std::collections::HashMap;
use glob::glob;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use crate::parser::SessionParser;
use crate::types::ParsedSession;
use crate::utils::path::encode_project_path;

// Keep the path-based snapshot for serialization
#[derive(Debug, Serialize, Deserialize)]
pub struct EnvironmentSnapshot {
    pub files: HashMap<PathBuf, String>,
    pub session_file: PathBuf,  // Store path for serialization
    pub timestamp: DateTime<Utc>,
    #[serde(skip)]  // Don't serialize the parsed session
    pub session: Option<ParsedSession>,  // Parsed on demand
}

// Manual Clone implementation
// Note: session is not cloned because ParsedSession doesn't implement Clone
// This means cloned snapshots lose their parsed session data
impl Clone for EnvironmentSnapshot {
    fn clone(&self) -> Self {
        Self {
            files: self.files.clone(),
            session_file: self.session_file.clone(),
            timestamp: self.timestamp,
            session: None,  // Can't clone ParsedSession - would need to re-parse from file
        }
    }
}

pub struct EnvironmentObserver {
    workspace: PathBuf,
    file_patterns: Vec<String>,
}

impl EnvironmentObserver {
    pub fn new(workspace: PathBuf) -> Self {
        Self {
            workspace: workspace.clone(),
            file_patterns: vec![
                "**/*.py".to_string(),
                "**/*.rs".to_string(),
                "**/*.js".to_string(),
                "**/*.ts".to_string(),
                "**/*.jsx".to_string(),
                "**/*.tsx".to_string(),
                "**/*.json".to_string(),
                "**/*.toml".to_string(),
                "**/*.yaml".to_string(),
                "**/*.yml".to_string(),
                "**/*.md".to_string(),
                "**/Dockerfile".to_string(),
                "**/.gitignore".to_string(),
            ],
        }
    }
    
    pub fn snapshot(&self) -> Result<EnvironmentSnapshot, ObserverError> {
        let files = self.snapshot_files()?;
        let session_file = self.find_active_session_file()?;
        
        // Parse the session
        let parser = SessionParser::new(&session_file);
        let session = parser.parse()
            .map_err(|e| ObserverError::ParseError(format!("Failed to parse session: {}", e)))
            .ok();  // Make it optional in case parsing fails
        
        Ok(EnvironmentSnapshot {
            files,
            session_file,
            timestamp: Utc::now(),
            session,
        })
    }
    
    // New method to snapshot with a known session ID
    pub fn snapshot_with_session(&self, session_id: &str) -> Result<EnvironmentSnapshot, ObserverError> {
        let files = self.snapshot_files()?;
        let session_file = self.find_session_file_by_id(session_id)?;
        
        // Parse the session
        let parser = SessionParser::new(&session_file);
        let session = parser.parse().ok();
        
        Ok(EnvironmentSnapshot {
            files,
            session_file,
            timestamp: Utc::now(),
            session,
        })
    }
    
    pub fn snapshot_files(&self) -> Result<HashMap<PathBuf, String>, ObserverError> {
        let mut files = HashMap::new();
        
        for pattern in &self.file_patterns {
            let full_pattern = self.workspace.join(pattern);
            let pattern_str = full_pattern.to_string_lossy();
            
            for entry in glob(&pattern_str).map_err(|e| ObserverError::GlobError(e.to_string()))? {
                match entry {
                    Ok(path) => {
                        // Skip directories and non-readable files
                        if path.is_file() {
                            if let Ok(content) = std::fs::read_to_string(&path) {
                                // Store relative path
                                if let Ok(relative) = path.strip_prefix(&self.workspace) {
                                    files.insert(relative.to_path_buf(), content);
                                }
                            }
                        }
                    }
                    Err(_) => continue,
                }
            }
        }
        
        Ok(files)
    }
    
    
    fn find_active_session_file(&self) -> Result<PathBuf, ObserverError> {
        let claude_projects = home::home_dir()
            .ok_or_else(|| ObserverError::HomeNotFound)?
            .join(".claude")
            .join("projects");
            
        // Convert workspace path to Claude's project naming pattern
        let project_name = encode_project_path(&self.workspace);
            
        let project_dir = claude_projects.join(&project_name);
        
        
        if !project_dir.exists() {
            return Err(ObserverError::ProjectNotFound(format!(
                "Project directory not found: {:?} (encoded from workspace: {:?})", 
                project_dir,
                self.workspace
            )));
        }
        
        // Find most recent session file
        let mut session_files: Vec<_> = std::fs::read_dir(&project_dir)
            .map_err(|e| ObserverError::IoError(e.to_string()))?
            .filter_map(|entry| entry.ok())
            .filter(|entry| {
                entry.path().extension()
                    .map(|ext| ext == "jsonl")
                    .unwrap_or(false)
            })
            .collect();
            
        session_files.sort_by_key(|entry| {
            entry.metadata()
                .and_then(|m| m.modified())
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
        });
        
        session_files
            .last()
            .map(|entry| entry.path())
            .ok_or_else(|| ObserverError::NoSessionFound)
    }
    
    fn find_session_file_by_id(&self, session_id: &str) -> Result<PathBuf, ObserverError> {
        let claude_projects = home::home_dir()
            .ok_or_else(|| ObserverError::HomeNotFound)?
            .join(".claude")
            .join("projects");
            
        // Convert workspace path to Claude's project naming pattern
        let project_name = encode_project_path(&self.workspace);
            
        let project_dir = claude_projects.join(&project_name);
        let session_file = project_dir.join(format!("{}.jsonl", session_id));
        
        if !session_file.exists() {
            return Err(ObserverError::NoSessionFound);
        }
        
        Ok(session_file)
    }
}

#[derive(Debug, thiserror::Error)]
pub enum ObserverError {
    #[error("Glob pattern error: {0}")]
    GlobError(String),
    
    #[error("Failed to parse session: {0}")]
    ParseError(String),
    
    #[error("Home directory not found")]
    HomeNotFound,
    
    #[error("Invalid workspace path")]
    InvalidWorkspace,
    
    #[error("Project not found: {0}")]
    ProjectNotFound(String),
    
    #[error("No session files found")]
    NoSessionFound,
    
    #[error("IO error: {0}")]
    IoError(String),
}