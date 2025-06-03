// Test session continuation functionality
// Run with: cargo test --test t1_continue_test -- --ignored --nocapture

mod common;

use claude_sdk::execution::ClaudeEnvironment;
use common::TestEnvironment;

#[test]
#[ignore]
fn test_session_continuation() {
    println!("\n=== Session Continuation Test ===\n");
    
    let env = TestEnvironment::setup();
    let mut claude_env = ClaudeEnvironment::new(env.workspace.clone()).unwrap();
    
    // First execution - create a file
    println!("1. First execution - creating initial file...");
    let transition1 = claude_env.execute(
        "Create a file called story.txt with 'Once upon a time'"
    ).unwrap();
    
    println!("   Session ID: {}", transition1.execution.session_id);
    println!("   Response: {}", transition1.execution.response);
    
    // Continue the session
    println!("\n2. Continuing session...");
    let transition2 = claude_env.execute_with_options(
        "Add ' there was a brave knight' to the story.txt file",
        true  // continue_session = true
    ).unwrap();
    
    println!("   Session ID: {}", transition2.execution.session_id);
    println!("   Response: {}", transition2.execution.response);
    
    // Check if it's a different session ID (as we discovered)
    println!("\n3. Analysis:");
    println!("   Same session ID: {}", transition1.execution.session_id == transition2.execution.session_id);
    println!("   Session 1 messages: {:?}", transition1.after.session.as_ref().map(|s| s.messages.len()));
    println!("   Session 2 messages: {:?}", transition2.after.session.as_ref().map(|s| s.messages.len()));
    
    // Check if Claude remembered the context
    let tools_used = transition2.tools_used();
    println!("   Tools used in continuation: {:?}", tools_used);
    
    println!("\n✅ Session continuation test completed!");
}