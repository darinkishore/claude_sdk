// Integration tests for T1 execution engine
// Requires Claude CLI to be installed
// Run with: cargo test --test t1_integration_test -- --ignored --nocapture

mod executor_integration_tests {
    use claude_sdk::execution::{ClaudeExecutor, ClaudePrompt};
    use tempfile::TempDir;

    #[test]
    #[ignore] // Run with: cargo test --test t1_integration_test -- --ignored
    fn test_claude_executor_basic_prompt() {
        // Create a temporary directory for the test
        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let workspace = temp_dir.path().to_path_buf();
        
        // Create executor
        let executor = ClaudeExecutor::new(workspace.clone())
            .expect("Failed to create ClaudeExecutor - is Claude CLI installed?");
        
        // Execute a simple prompt
        let prompt = ClaudePrompt {
            text: "Create a file called test.txt with the content 'Hello from Claude'".to_string(),
            continue_session: false,
            resume_session_id: None,
        };
        
        let execution = executor.execute(prompt.clone())
            .expect("Failed to execute prompt");
        
        // Print debug info
        println!("Execution response: {}", execution.response);
        println!("Session ID: {}", execution.session_id);
        println!("Working directory: {:?}", workspace);
        
        // Verify response
        assert!(!execution.response.is_empty(), "Response should not be empty");
        assert!(!execution.session_id.is_empty(), "Session ID should not be empty");
        assert!(execution.cost > 0.0, "Cost should be greater than 0");
        assert!(execution.duration_ms > 0, "Duration should be greater than 0");
        
        // Wait a bit for file system to settle
        std::thread::sleep(std::time::Duration::from_secs(1));
        
        // List files in the directory
        println!("\nFiles in workspace:");
        for entry in std::fs::read_dir(&workspace).unwrap() {
            if let Ok(entry) = entry {
                println!("  - {:?}", entry.path());
            }
        }
        
        // Verify the file was created
        let test_file = workspace.join("test.txt");
        assert!(test_file.exists(), "test.txt should have been created");
        
        let content = std::fs::read_to_string(&test_file)
            .expect("Failed to read test.txt");
        assert!(content.contains("Hello from Claude"), "File should contain expected text");
        
        println!("✅ ClaudeExecutor basic test passed!");
        println!("   Response: {}", &execution.response[..100.min(execution.response.len())]);
        println!("   Session ID: {}", execution.session_id);
        println!("   Cost: ${:.4}", execution.cost);
        println!("   Duration: {}ms", execution.duration_ms);
    }
    
    #[test]
    #[ignore]
    fn test_claude_executor_continue_session() {
        let temp_dir = TempDir::new().expect("Failed to create temp dir");
        let workspace = temp_dir.path().to_path_buf();
        
        let executor = ClaudeExecutor::new(workspace.clone())
            .expect("Failed to create ClaudeExecutor");
        
        // First prompt - start a session
        let prompt1 = ClaudePrompt {
            text: "Create a Python file called hello.py with a function that prints 'Hello'".to_string(),
            continue_session: false,
            resume_session_id: None,
        };
        
        let execution1 = executor.execute(prompt1)
            .expect("Failed to execute first prompt");
        
        let session_id1 = execution1.session_id.clone();
        
        // Second prompt - continue the session
        let prompt2 = ClaudePrompt {
            text: "Now add a main block that calls the hello function".to_string(),
            continue_session: true,
            resume_session_id: None,
        };
        
        let execution2 = executor.execute(prompt2)
            .expect("Failed to execute continuation prompt");
        
        // Note: Claude creates a new session ID for each execution, even with --continue
        // The session_id will be different, but the conversation context is maintained
        assert_ne!(execution2.session_id, session_id1, 
            "Session ID should be different even when continuing");
        
        // Verify the file was updated
        let hello_file = workspace.join("hello.py");
        assert!(hello_file.exists(), "hello.py should exist");
        
        let content = std::fs::read_to_string(&hello_file)
            .expect("Failed to read hello.py");
        assert!(content.contains("def"), "Should contain function definition");
        assert!(content.contains("if __name__"), "Should contain main block");
        
        println!("✅ ClaudeExecutor continue session test passed!");
    }
}