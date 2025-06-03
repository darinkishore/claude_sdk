// Test tool permission configuration
// Run with: cargo test --test t1_tool_permissions_test -- --ignored --nocapture

use claude_sdk::execution::{ClaudeExecutor, ClaudePrompt};
use tempfile::TempDir;

#[test]
#[ignore]
fn test_tool_permissions() {
    println!("\n=== Tool Permissions Test ===\n");
    
    let temp_dir = TempDir::new().unwrap();
    let workspace = temp_dir.path().to_path_buf();
    
    // Test 1: Default behavior (currently --dangerously-skip-permissions)
    println!("1. Testing default permissions...");
    let executor = ClaudeExecutor::new(workspace.clone()).unwrap();
    let result = executor.execute(ClaudePrompt {
        text: "Create a file test.txt".to_string(),
        continue_session: false,
        resume_session_id: None,
    });
    
    match result {
        Ok(exec) => println!("   ✅ Default execution succeeded: {}", exec.response),
        Err(e) => println!("   ❌ Default execution failed: {}", e),
    }
    
    // Test 2: With allowed tools
    println!("\n2. Testing with allowed tools...");
    let mut executor2 = ClaudeExecutor::new(workspace.clone()).unwrap();
    executor2.set_allowed_tools(Some("Read,Write".to_string()));
    
    let result2 = executor2.execute(ClaudePrompt {
        text: "Create another file allowed.txt".to_string(),
        continue_session: false,
        resume_session_id: None,
    });
    
    match result2 {
        Ok(exec) => println!("   ✅ Allowed tools execution succeeded: {}", exec.response),
        Err(e) => println!("   ❌ Allowed tools execution failed: {}", e),
    }
    
    // Test 3: With disallowed tools
    println!("\n3. Testing with disallowed tools...");
    let mut executor3 = ClaudeExecutor::new(workspace.clone()).unwrap();
    executor3.set_disallowed_tools(Some("Bash".to_string()));
    executor3.set_allowed_tools(Some("*".to_string())); // Allow all except Bash
    
    let result3 = executor3.execute(ClaudePrompt {
        text: "List files using Read tool, not Bash".to_string(),
        continue_session: false,
        resume_session_id: None,
    });
    
    match result3 {
        Ok(exec) => println!("   ✅ Disallowed tools execution succeeded: {}", exec.response),
        Err(e) => println!("   ❌ Disallowed tools execution failed: {}", e),
    }
    
    // Test 4: Specific tool with arguments
    println!("\n4. Testing specific tool with arguments...");
    let mut executor4 = ClaudeExecutor::new(workspace.clone()).unwrap();
    executor4.set_allowed_tools(Some("Bash(ls),Read,Write".to_string()));
    
    let result4 = executor4.execute(ClaudePrompt {
        text: "Use ls to list files".to_string(),
        continue_session: false,
        resume_session_id: None,
    });
    
    match result4 {
        Ok(exec) => println!("   ✅ Specific command execution succeeded: {}", exec.response),
        Err(e) => println!("   ❌ Specific command execution failed: {}", e),
    }
    
    println!("\n=== Tool Permissions Documentation ===");
    println!("Format examples:");
    println!("  - Allow specific tools: \"Read,Write,Edit\"");
    println!("  - Allow all tools: \"*\"");
    println!("  - Allow specific Bash commands: \"Bash(npm install),Bash(npm test)\"");
    println!("  - Disallow specific tools: set_disallowed_tools(\"Bash,WebFetch\")");
    println!("\nCurrent behavior:");
    println!("  - Default: --dangerously-skip-permissions (TODO: change this)");
    println!("  - With allowed_tools set: uses --allowedTools flag");
    println!("  - With disallowed_tools set: uses --disallowedTools flag");
    println!("  - With both set: both flags are passed to Claude");
}