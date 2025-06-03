// Test disallowing specific tools while allowing others
// Run with: cargo test --test t1_disallow_test -- --ignored --nocapture

mod common;

use std::sync::Arc;
use claude_sdk::execution::{Workspace, Conversation};
use common::TestEnvironment;

#[test]
#[ignore]
fn test_disallow_specific_tools() {
    println!("\n=== Disallow Specific Tools Test ===\n");
    
    let env = TestEnvironment::setup();
    let mut workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    
    // Test 1: Disallow Write but allow Read
    println!("1. Testing with Write disallowed...");
    Arc::get_mut(&mut workspace).unwrap().set_disallowed_tools(Some("Write".to_string()));
    
    let mut conversation = Conversation::new(workspace.clone());
    let result = conversation.send(
        "Try to create a file test.txt with 'Hello World' content"
    );
    
    match result {
        Ok(transition) => {
            println!("   Response: {}", transition.execution.response);
            if transition.execution.response.contains("not allowed") || 
               transition.execution.response.contains("permission") {
                println!("   ✅ Claude correctly identified that Write is not allowed");
            } else {
                println!("   ⚠️  Claude didn't explicitly mention permission issue");
            }
        },
        Err(e) => println!("   ❌ Execution failed: {}", e),
    }
    
    // Test 2: Now try with MultiEdit (should work as alternative)
    println!("\n2. Testing with MultiEdit as alternative...");
    let result2 = conversation.send(
        "Use MultiEdit to create a file test.txt with 'Hello World' content"
    );
    
    match result2 {
        Ok(transition) => {
            println!("   Response: {}", transition.execution.response);
            println!("   Tools used: {:?}", transition.tools_used());
            if transition.tools_used().contains(&"MultiEdit".to_string()) {
                println!("   ✅ Claude successfully used MultiEdit as alternative");
            }
        },
        Err(e) => println!("   ❌ Execution failed: {}", e),
    }
    
    // Test 3: Disallow all file writing tools
    println!("\n3. Testing with all write tools disallowed...");
    let mut workspace2 = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    Arc::get_mut(&mut workspace2).unwrap().set_disallowed_tools(Some("Write,MultiEdit,Edit".to_string()));
    
    let mut conversation2 = Conversation::new(workspace2);
    let result3 = conversation2.send(
        "Create a file called blocked.txt"
    );
    
    match result3 {
        Ok(transition) => {
            println!("   Response: {}", transition.execution.response);
            println!("   ✅ Claude handled the restriction gracefully");
        },
        Err(e) => println!("   ❌ Execution failed: {}", e),
    }
    
    println!("\n✅ Disallow tools test completed!");
}

#[test]
#[ignore]
fn test_restricted_bash_commands() {
    println!("\n=== Restricted Bash Commands Test ===\n");
    
    let env = TestEnvironment::setup();
    let mut workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    
    // Allow only specific bash commands
    println!("1. Testing with only ls and echo allowed for Bash...");
    Arc::get_mut(&mut workspace).unwrap().set_allowed_tools(
        Some("Bash(ls),Bash(echo),Read,Write".to_string())
    );
    
    let mut conversation = Conversation::new(workspace.clone());
    
    // Try allowed command
    let result1 = conversation.send("List the files in the current directory");
    match result1 {
        Ok(transition) => {
            println!("   ✅ ls command succeeded: {}", transition.execution.response);
        },
        Err(e) => println!("   ❌ ls command failed: {}", e),
    }
    
    // Try disallowed command
    println!("\n2. Testing with disallowed rm command...");
    let result2 = conversation.send("Remove any temporary files using rm");
    match result2 {
        Ok(transition) => {
            println!("   Response: {}", transition.execution.response);
            if transition.execution.response.contains("not allowed") || 
               transition.execution.response.contains("permission") {
                println!("   ✅ Claude correctly identified that rm is not allowed");
            }
        },
        Err(e) => println!("   ❌ Execution failed: {}", e),
    }
    
    println!("\n✅ Restricted bash commands test completed!");
}