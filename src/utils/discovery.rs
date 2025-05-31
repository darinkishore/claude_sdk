use std::path::{Path, PathBuf};
use std::fs;

use crate::error::ClaudeError;

/// Find all JSONL session files in a directory
pub fn discover_sessions(base_path: &Path, project_filter: Option<&str>) -> Result<Vec<PathBuf>, ClaudeError> {
    let mut sessions = Vec::new();
    
    if !base_path.exists() {
        return Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Directory not found: {}", base_path.display())
        ).into());
    }
    
    // If project filter is provided, look only in that project directory
    if let Some(project) = project_filter {
        let project_path = base_path.join(project);
        if project_path.exists() && project_path.is_dir() {
            collect_jsonl_files(&project_path, &mut sessions)?;
        }
    } else {
        // Otherwise, recursively search all subdirectories
        collect_jsonl_files_recursive(base_path, &mut sessions)?;
    }
    
    // Sort by modification time (most recent first)
    sessions.sort_by_key(|path| {
        fs::metadata(path)
            .and_then(|m| m.modified())
            .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
    });
    sessions.reverse();
    
    Ok(sessions)
}

/// Find all project directories in the base path
pub fn discover_projects(base_path: &Path) -> Result<Vec<PathBuf>, ClaudeError> {
    let mut projects = Vec::new();
    
    if !base_path.exists() {
        return Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Directory not found: {}", base_path.display())
        ).into());
    }
    
    // Find all directories that start with "-" (Claude Code encoding)
    for entry in fs::read_dir(base_path)? {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_dir() {
            if let Some(name) = path.file_name() {
                if let Some(name_str) = name.to_str() {
                    if name_str.starts_with('-') {
                        projects.push(path);
                    }
                }
            }
        }
    }
    
    // Sort by modification time (most recent first)
    projects.sort_by_key(|path| {
        fs::metadata(path)
            .and_then(|m| m.modified())
            .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
    });
    projects.reverse();
    
    Ok(projects)
}

/// Collect JSONL files in a single directory (non-recursive)
fn collect_jsonl_files(dir: &Path, sessions: &mut Vec<PathBuf>) -> Result<(), ClaudeError> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_file() {
            if let Some(ext) = path.extension() {
                if ext == "jsonl" {
                    sessions.push(path);
                }
            }
        }
    }
    Ok(())
}

/// Recursively collect JSONL files from all subdirectories
fn collect_jsonl_files_recursive(dir: &Path, sessions: &mut Vec<PathBuf>) -> Result<(), ClaudeError> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_dir() {
            collect_jsonl_files_recursive(&path, sessions)?;
        } else if path.is_file() {
            if let Some(ext) = path.extension() {
                if ext == "jsonl" {
                    sessions.push(path);
                }
            }
        }
    }
    Ok(())
}

/// Get the default Claude projects directory
pub fn default_projects_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".claude")
        .join("projects")
}