use std::path::PathBuf;
use std::collections::HashMap;
use glob::glob;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentSnapshot {
    pub files: HashMap<PathBuf, String>,
    pub session_file: PathBuf,  // Path to the session file instead of parsed data
    pub timestamp: DateTime<Utc>,
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
        
        Ok(EnvironmentSnapshot {
            files,
            session_file,
            timestamp: Utc::now(),
        })
    }
    
    fn snapshot_files(&self) -> Result<HashMap<PathBuf, String>, ObserverError> {
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
            
        // Find project directory matching our workspace
        let workspace_name = self.workspace
            .file_name()
            .ok_or_else(|| ObserverError::InvalidWorkspace)?
            .to_string_lossy();
            
        let project_dir = claude_projects.join(&*workspace_name);
        
        if !project_dir.exists() {
            return Err(ObserverError::ProjectNotFound(workspace_name.to_string()));
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