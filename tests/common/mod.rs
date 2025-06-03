// Common test utilities for T1 integration tests
// Provides a fixed test environment at ~/.claude-sdk/test-environment

use std::path::PathBuf;
use std::fs;
use std::env;

pub struct TestEnvironment {
    pub base_dir: PathBuf,        // ~/.claude-sdk/test-environment
    pub workspace: PathBuf,       // ~/.claude-sdk/test-environment/test-workspace
    pub claude_project: Option<PathBuf>, // Will be discovered
}

impl TestEnvironment {
    pub fn setup() -> Self {
        let home = env::var("HOME").expect("HOME environment variable not set");
        let base_dir = PathBuf::from(home).join(".claude-sdk").join("test-environment");
        let workspace = base_dir.join("test-workspace");
        
        // Create directories
        fs::create_dir_all(&workspace).expect("Failed to create test workspace");
        
        // Clean workspace contents (but keep the directory)
        if workspace.exists() {
            for entry in fs::read_dir(&workspace).unwrap() {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_dir() {
                        fs::remove_dir_all(path).ok();
                    } else {
                        fs::remove_file(path).ok();
                    }
                }
            }
        }
        
        println!("Test environment setup:");
        println!("  Base: {:?}", base_dir);
        println!("  Workspace: {:?}", workspace);
        
        Self {
            base_dir,
            workspace,
            claude_project: None,
        }
    }
    
    pub fn discover_claude_project(&mut self) -> Result<PathBuf, String> {
        // After running Claude, find where it created the project
        let claude_base = PathBuf::from(env::var("HOME").unwrap())
            .join(".claude")
            .join("projects");
            
        println!("Searching for Claude project in: {:?}", claude_base);
        
        // List all directories to find our test project
        if claude_base.exists() {
            for entry in fs::read_dir(&claude_base).map_err(|e| e.to_string())? {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_dir() {
                        let dir_name = path.file_name().unwrap().to_string_lossy();
                        println!("  Found project: {}", dir_name);
                        
                        // Check if this might be our test project
                        if dir_name.contains("test-environment") || dir_name.contains("test-workspace") {
                            println!("  -> This looks like our test project!");
                            self.claude_project = Some(path.clone());
                            return Ok(path);
                        }
                    }
                }
            }
        }
        
        Err("Could not find Claude project directory".to_string())
    }
    
    pub fn find_session_file(&self) -> Result<PathBuf, String> {
        let project_dir = self.claude_project.as_ref()
            .ok_or("Claude project not discovered yet")?;
            
        // Find the most recent .jsonl file
        let mut jsonl_files = Vec::new();
        for entry in fs::read_dir(project_dir).map_err(|e| e.to_string())? {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.extension().and_then(|s| s.to_str()) == Some("jsonl") {
                    jsonl_files.push(path);
                }
            }
        }
        
        // Sort by modification time (newest first)
        jsonl_files.sort_by_key(|path| {
            fs::metadata(path)
                .and_then(|m| m.modified())
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
        });
        jsonl_files.reverse();
        
        jsonl_files.into_iter().next()
            .ok_or("No session files found".to_string())
    }
    
    pub fn teardown(&self) {
        // Clean up test workspace
        if self.workspace.exists() {
            println!("Cleaning up test workspace: {:?}", self.workspace);
            // Don't remove the directory itself, just its contents
            for entry in fs::read_dir(&self.workspace).unwrap() {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_dir() {
                        fs::remove_dir_all(path).ok();
                    } else {
                        fs::remove_file(path).ok();
                    }
                }
            }
        }
        
        // Note: We don't clean up Claude's project directory as it might be reused
    }
}

impl Drop for TestEnvironment {
    fn drop(&mut self) {
        // Auto cleanup when test ends
        self.teardown();
    }
}