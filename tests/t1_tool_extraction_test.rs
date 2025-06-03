// Test tool extraction from transitions
// Run with: cargo test --test t1_tool_extraction_test -- --ignored --nocapture

mod common;

use claude_sdk::execution::{ClaudeEnvironment};
use common::TestEnvironment;

#[test]
#[ignore]
fn test_tool_extraction() {
    println!("\n=== Tool Extraction Test ===\n");
    
    let env = TestEnvironment::setup();
    let mut claude_env = ClaudeEnvironment::new(env.workspace.clone()).unwrap();
    
    // Execute a prompt that will use multiple tools
    println!("1. Executing prompt with tool usage...");
    let transition = claude_env.execute(
        "Create a Python file called calculator.py with add and multiply functions, then read it back to verify"
    ).unwrap();
    
    println!("   Response: {}", transition.execution.response);
    println!("   Cost: ${}", transition.execution.cost);
    
    // Extract tool information
    println!("\n2. Analyzing tool usage:");
    
    // Debug session info
    println!("   Execution session ID: {}", transition.execution.session_id);
    println!("   Before session file: {:?}", transition.before.session_file);
    println!("   Before session: {:?}", transition.before.session.as_ref().map(|s| s.messages.len()));
    println!("   After session file: {:?}", transition.after.session_file);
    println!("   After session: {:?}", transition.after.session.as_ref().map(|s| s.messages.len()));
    
    // Get new messages
    let new_messages = transition.new_messages();
    println!("   New messages: {}", new_messages.len());
    
    // Debug what's in the messages
    for (i, msg) in new_messages.iter().enumerate() {
        println!("\n   Message {}: role={:?}, type={:?}", 
            i + 1, msg.message.role, msg.message_type);
        for (j, content) in msg.message.content.iter().enumerate() {
            println!("     Content {}: {:?}", j + 1, content);
        }
    }
    
    // Get tool executions
    let tool_execs = transition.tool_executions();
    println!("   Tool executions: {}", tool_execs.len());
    
    for (i, exec) in tool_execs.iter().enumerate() {
        println!("\n   Tool execution {}:", i + 1);
        println!("     Name: {}", exec.tool_name);
        println!("     Success: {}", exec.is_success());
        println!("     Duration: {}ms", exec.duration_ms());
        println!("     Input: {}", serde_json::to_string_pretty(&exec.input).unwrap());
        if !exec.output.content.is_empty() {
            println!("     Output preview: {}", 
                exec.output.content.chars().take(100).collect::<String>());
        }
    }
    
    // Get just tool names
    let tools_used = transition.tools_used();
    println!("\n3. Tools used: {:?}", tools_used);
    
    // Check for errors
    let has_errors = transition.has_tool_errors();
    println!("\n4. Had tool errors: {}", has_errors);
    
    // Verify expected tools were used
    assert!(tools_used.contains(&"Write".to_string()) || 
            tools_used.contains(&"MultiEdit".to_string()), 
            "Should have used Write or MultiEdit tool");
    assert!(tools_used.contains(&"Read".to_string()), 
            "Should have used Read tool to verify");
    
    println!("\n✅ Tool extraction test passed!");
}