// Test session continuation functionality
// Run with: cargo test --test t1_continue_test -- --ignored --nocapture

mod common;

use std::sync::{Arc, Mutex};
use claude_sdk::execution::{Workspace, Conversation};
use common::TestEnvironment;

#[test]
#[ignore]
fn test_session_continuation() {
    println!("\n=== Session Continuation Test ===\n");
    
    let env = TestEnvironment::setup();
    let workspace = Arc::new(Mutex::new(Workspace::new(env.workspace.clone()).unwrap()));
    let mut conversation = Conversation::new(workspace);
    
    // First execution - create a file
    println!("1. First execution - creating initial file...");
    let transition1 = conversation.send(
        "Create a file called story.txt with 'Once upon a time'"
    ).unwrap();
    
    println!("   Session ID: {}", transition1.execution.session_id);
    println!("   Response: {}", transition1.execution.response);
    
    // Continue the session
    println!("\n2. Continuing session...");
    let transition2 = conversation.send(
        "Add ' there was a brave knight' to the story.txt file"
    ).unwrap();
    
    println!("   Session ID: {}", transition2.execution.session_id);
    println!("   Response: {}", transition2.execution.response);
    
    // Check if it's a different session ID (as we discovered)
    println!("\n3. Analysis:");
    println!("   Same session ID: {}", transition1.execution.session_id == transition2.execution.session_id);
    println!("   Total transitions: {}", conversation.history().len());
    println!("   Session IDs: {:?}", conversation.session_ids());
    println!("   Total cost: ${}", conversation.total_cost());
    
    // Check if Claude remembered the context
    let tools_used = conversation.tools_used();
    println!("   Tools used in conversation: {:?}", tools_used);
    
    println!("\n✅ Session continuation test completed!");
}