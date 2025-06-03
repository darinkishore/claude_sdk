use pyo3::prelude::*;
use pyo3::exceptions::PyFileNotFoundError;
use std::path::{Path, PathBuf};

use crate::{SessionParser, ClaudeError};
use crate::utils::{discover_sessions as rust_discover_sessions, discover_projects as rust_discover_projects, default_projects_dir};
use super::classes::{Session, Project};
use super::exceptions::{ParseError, SessionError};

/// Load a Claude Code session from a JSONL file.
/// 
/// This function parses a Claude Code session file and returns a Session object
/// with all messages, metadata, and tool usage information.
/// 
/// Args:
///     file_path: Path to the JSONL session file
/// 
/// Returns:
///     Session: Complete session object with messages and metadata
/// 
/// Raises:
///     ParseError: If the file cannot be parsed due to invalid format
///     FileNotFoundError: If the specified file does not exist
///     ClaudeSDKError: Base class for all SDK-specific exceptions
/// 
/// Example:
///     >>> from claude_sdk import load
///     >>> session = load("conversation.jsonl")
///     >>> print(f"Session ID: {session.session_id}")
///     >>> print(f"Total cost: ${session.total_cost:.4f}")
#[pyfunction]
#[pyo3(text_signature = "(file_path)")]
pub fn load(_py: Python<'_>, file_path: &Bound<'_, PyAny>) -> PyResult<Session> {
    // Convert file_path to string, handling both str and Path objects
    let path_str = if let Ok(s) = file_path.extract::<String>() {
        s
    } else if let Ok(path_obj) = file_path.getattr("__str__") {
        path_obj.call0()?.extract::<String>()?
    } else {
        return Err(pyo3::exceptions::PyTypeError::new_err(
            "file_path must be a string or Path-like object"
        ));
    };
    
    // Check if file exists
    let path = Path::new(&path_str);
    if !path.exists() {
        return Err(PyFileNotFoundError::new_err(format!(
            "Session file not found: {}", path_str
        )));
    }
    
    // Parse the session using our Rust parser
    let parser = SessionParser::new(path);
    let parsed_session = match parser.parse() {
        Ok(session) => session,
        Err(e) => match e {
            ClaudeError::ParseError(_) => return Err(ParseError::new_err(format!(
                "Failed to parse session: {}", e
            ))),
            ClaudeError::ExecutionError(_) => return Err(SessionError::new_err(format!(
                "Session processing error: {}", e
            ))),
            ClaudeError::SessionNotFound { .. } => return Err(PyFileNotFoundError::new_err(format!(
                "Session not found: {}", e
            ))),
            ClaudeError::IoError(_) => return Err(PyFileNotFoundError::new_err(format!(
                "IO error: {}", e
            ))),
            ClaudeError::JsonError(_) => return Err(ParseError::new_err(format!(
                "JSON error: {}", e
            ))),
        }
    };
    
    Ok(Session::from_rust_session(parsed_session))
}

/// Find Claude Code session files.
/// 
/// This function discovers all Claude Code JSONL session files, either in the
/// specified base directory or filtered to a specific project.
/// 
/// Args:
///     base_path: Directory to search (defaults to ~/.claude/projects/)
///     project: Optional project name/path to filter by
/// 
/// Returns:
///     List of paths to JSONL session files
/// 
/// Raises:
///     ParseError: If the directory doesn't exist or can't be accessed
#[pyfunction]
#[pyo3(signature = (base_path=None, project=None))]  
pub fn find_sessions(base_path: Option<&str>, project: Option<&str>) -> PyResult<Vec<String>> {
    // Determine the base path
    let search_path = match base_path {
        Some(path_str) => PathBuf::from(path_str),
        None => default_projects_dir(),
    };
    
    // Discover sessions
    let sessions = rust_discover_sessions(&search_path, project)
        .map_err(|e| ParseError::new_err(format!(
            "Failed to discover sessions: {}", e
        )))?;
    
    // Convert paths to strings
    let session_paths: Vec<String> = sessions
        .into_iter()
        .filter_map(|path| path.to_str().map(|s| s.to_string()))
        .collect();
    
    Ok(session_paths)
}

/// Find Claude Code project directories.
/// 
/// This function discovers all Claude Code project directories in the specified
/// base directory or in the default ~/.claude/projects/ directory.
/// 
/// Args:
///     base_path: Directory to search (defaults to ~/.claude/projects/)
/// 
/// Returns:
///     List of paths to project directories
/// 
/// Raises:
///     ParseError: If the directory doesn't exist or can't be accessed
#[pyfunction]
#[pyo3(signature = (base_path=None))]
pub fn find_projects(base_path: Option<&str>) -> PyResult<Vec<String>> {
    // Determine the base path
    let search_path = match base_path {
        Some(path_str) => PathBuf::from(path_str),
        None => default_projects_dir(),
    };
    
    // Discover projects
    let projects = rust_discover_projects(&search_path)
        .map_err(|e| ParseError::new_err(format!(
            "Failed to discover projects: {}", e
        )))?;
    
    // Convert paths to strings
    let project_paths: Vec<String> = projects
        .into_iter()
        .filter_map(|path| path.to_str().map(|s| s.to_string()))
        .collect();
    
    Ok(project_paths)
}

/// Load a Claude Code project by name or path.
/// 
/// This function loads a Claude Code project, either by name (e.g., 'apply-model')
/// or by full path. It discovers all session files in the project directory and
/// loads them into a Project object.
/// 
/// Args:
///     project_identifier: Project name or full path
///     base_path: Base directory to search in (defaults to ~/.claude/projects/)
/// 
/// Returns:
///     Project: Project object with all sessions loaded
/// 
/// Raises:
///     ParseError: If project cannot be found or sessions cannot be loaded
#[pyfunction]
#[pyo3(signature = (project_identifier, base_path=None))]
pub fn load_project(project_identifier: &str, base_path: Option<&str>) -> PyResult<Project> {
    // Determine the base path
    let search_base = match base_path {
        Some(path_str) => PathBuf::from(path_str),
        None => default_projects_dir(),
    };
    
    // Check if project_identifier is a full path or just a name
    let project_path = if project_identifier.contains('/') || project_identifier.contains('\\') {
        // It's a full path
        PathBuf::from(project_identifier)
    } else {
        // It's a project name - find it in the base directory
        let mut found_path = None;
        
        // Look for project directory matching the name
        let projects = rust_discover_projects(&search_base)
            .map_err(|e| ParseError::new_err(format!(
                "Failed to discover projects: {}", e
            )))?;
        
        for project_dir in projects {
            if let Some(dir_name) = project_dir.file_name() {
                if let Some(name_str) = dir_name.to_str() {
                    // Check if the encoded project name contains the identifier
                    if name_str.contains(project_identifier) {
                        found_path = Some(project_dir);
                        break;
                    }
                }
            }
        }
        
        match found_path {
            Some(path) => path,
            None => return Err(ParseError::new_err(format!(
                "Project '{}' not found in {}", project_identifier, search_base.display()
            ))),
        }
    };
    
    // Verify the project path exists
    if !project_path.exists() {
        return Err(PyFileNotFoundError::new_err(format!(
            "Project directory not found: {}", project_path.display()
        )));
    }
    
    // Get project name from path
    let project_name = project_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();
    
    // Discover all session files in the project
    let session_files = rust_discover_sessions(&project_path, None)
        .map_err(|e| ParseError::new_err(format!(
            "Failed to discover sessions in project: {}", e
        )))?;
    
    // Load all sessions
    let mut sessions = Vec::new();
    for session_path in session_files {
        // Parse each session
        let parser = SessionParser::new(&session_path);
        match parser.parse() {
            Ok(parsed_session) => {
                sessions.push(Session::from_rust_session(parsed_session));
            }
            Err(e) => {
                // Log warning but continue loading other sessions
                tracing::warn!(
                    "Failed to parse session {}: {}",
                    session_path.display(),
                    e
                );
            }
        }
    }
    
    // Create and return the Project
    Python::with_gil(|py| Project::new(py, project_name, sessions))
}