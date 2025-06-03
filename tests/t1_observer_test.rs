// Integration tests for EnvironmentObserver
// Run with: cargo test --test t1_observer_test -- --ignored --nocapture
//
// NOTE: These tests are tricky because EnvironmentObserver looks for Claude session files
// in ~/.claude/projects/{workspace_name}/, not in the workspace itself.
// We need to either:
// 1. Use a real directory name that might have Claude sessions
// 2. Mock the session file location (requires refactoring)
// 3. Test only the file snapshot functionality

use claude_sdk::execution::EnvironmentObserver;
use std::path::PathBuf;
use tempfile::TempDir;
use std::fs;

#[test]
#[ignore]
fn test_environment_observer_file_snapshot_only() {
    // This test focuses on the file snapshot functionality
    // Testing session discovery is complex because Claude writes to ~/.claude/projects/
    
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    let workspace = temp_dir.path().to_path_buf();
    
    // Create test files
    fs::write(workspace.join("main.py"), "print('hello')").unwrap();
    fs::write(workspace.join("config.json"), r#"{"test": true}"#).unwrap();
    fs::create_dir(workspace.join("src")).unwrap();
    fs::write(workspace.join("src/app.js"), "console.log('hi')").unwrap();
    
    // Create files that should be ignored
    fs::write(workspace.join("data.txt"), "ignored").unwrap();
    fs::write(workspace.join("binary.exe"), "binary").unwrap();
    
    // Create observer
    let observer = EnvironmentObserver::new(workspace.clone());
    
    // We can't test the full snapshot() method without a real Claude session
    // But we can test the internal file snapshot functionality
    // For now, let's just verify the observer was created successfully
    
    println!("✅ EnvironmentObserver created successfully");
    println!("   Workspace: {:?}", workspace);
    
    // The real test would require either:
    // 1. Running Claude first in a known directory
    // 2. Mocking the session file discovery
    // 3. Refactoring to make session discovery injectable
}

#[test]
#[ignore]
fn test_environment_observer_file_patterns() {
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    let workspace = temp_dir.path().to_path_buf();
    
    // Create various file types
    std::fs::write(workspace.join("script.py"), "# Python file").unwrap();
    std::fs::write(workspace.join("app.js"), "// JavaScript file").unwrap();
    std::fs::write(workspace.join("README.md"), "# Documentation").unwrap();
    std::fs::write(workspace.join("data.txt"), "Should not be captured").unwrap();
    std::fs::write(workspace.join("binary.exe"), "Binary content").unwrap();
    
    // Create nested structure
    std::fs::create_dir_all(workspace.join("nested/deep")).unwrap();
    std::fs::write(workspace.join("nested/deep/module.py"), "# Nested Python").unwrap();
    
    // Create observer
    let observer = EnvironmentObserver::new(workspace.clone());
    
    // Create a Claude session first
    let executor = ClaudeExecutor::new(workspace.clone()).unwrap();
    executor.execute(ClaudePrompt {
        text: "List files".to_string(),
        continue_session: false,
    }).unwrap();
    
    std::thread::sleep(std::time::Duration::from_secs(1));
    
    // Take snapshot
    let snapshot = observer.snapshot().expect("Failed to take snapshot");
    
    // Verify correct files were captured
    assert!(snapshot.files.contains_key(&PathBuf::from("script.py")));
    assert!(snapshot.files.contains_key(&PathBuf::from("app.js")));
    assert!(snapshot.files.contains_key(&PathBuf::from("README.md")));
    assert!(snapshot.files.contains_key(&PathBuf::from("nested/deep/module.py")));
    
    // Verify excluded files were not captured
    assert!(!snapshot.files.contains_key(&PathBuf::from("data.txt")));
    assert!(!snapshot.files.contains_key(&PathBuf::from("binary.exe")));
    
    println!("✅ File pattern test passed!");
    println!("   Captured files:");
    for (path, _) in &snapshot.files {
        println!("     - {:?}", path);
    }
}