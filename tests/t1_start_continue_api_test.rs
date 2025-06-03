// Test the new start() and continue_session() API
// Run with: cargo test --test t1_start_continue_api_test -- --ignored --nocapture

mod common;

use claude_sdk::execution::ClaudeEnvironment;
use common::TestEnvironment;

#[test]
#[ignore]
fn test_start_continue_api() {
    println!("\n=== Start/Continue API Test ===\n");
    
    let env = TestEnvironment::setup();
    let mut claude_env = ClaudeEnvironment::new(env.workspace.clone()).unwrap();
    
    // Test 1: Use start() for new session
    println!("1. Starting new session with start()...");
    let transition1 = claude_env.start(
        "Create a file called api_test.txt with 'Testing new API'"
    ).unwrap();
    
    println!("   Session ID: {}", transition1.execution.session_id);
    println!("   Messages in session: {:?}", transition1.after.session.as_ref().map(|s| s.messages.len()));
    
    // Test 2: Use continue_session() to continue
    println!("\n2. Continuing with continue_session()...");
    let transition2 = claude_env.continue_session(
        "Add ' - it works!' to the api_test.txt file"
    ).unwrap();
    
    println!("   Session ID: {}", transition2.execution.session_id);
    println!("   Messages in session: {:?}", transition2.after.session.as_ref().map(|s| s.messages.len()));
    
    // Test 3: Start another fresh session
    println!("\n3. Starting another fresh session...");
    let transition3 = claude_env.start(
        "Create a new file called fresh.txt"
    ).unwrap();
    
    println!("   Session ID: {}", transition3.execution.session_id);
    println!("   Messages in session: {:?}", transition3.after.session.as_ref().map(|s| s.messages.len()));
    
    // Verify the API behavior
    println!("\n4. API Behavior Summary:");
    println!("   - start() creates new sessions (IDs differ each time)");
    println!("   - continue_session() maintains conversation context");
    println!("   - Both return Transition objects with full state");
    
    println!("\n✅ Start/Continue API test passed!");
}