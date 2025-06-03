// Test the new Conversation-centric API
// Run with: cargo test --test t1_conversation_v2_test -- --ignored --nocapture

mod common;

use std::sync::Arc;
use claude_sdk::execution::{Workspace, Conversation};
use common::TestEnvironment;

#[test]
#[ignore]
fn test_conversation_owns_transitions() {
    println!("\n=== Conversation V2 Test ===\n");
    
    let env = TestEnvironment::setup();
    let workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    
    // Create a conversation
    let mut conversation = Conversation::new(workspace.clone());
    println!("1. Created conversation: {}", conversation.id());
    
    // Send first message
    println!("\n2. Sending first message...");
    let t1 = conversation.send("Create a file called test.txt with 'Hello from conversation'").unwrap();
    println!("   Response: {}", t1.execution.response);
    println!("   Session ID: {}", t1.execution.session_id);
    println!("   Transition ID: {}", t1.id);
    
    // Send second message
    println!("\n3. Continuing conversation...");
    let t2 = conversation.send("Add ' - it works!' to test.txt").unwrap();
    println!("   Response: {}", t2.execution.response);
    println!("   Session ID: {}", t2.execution.session_id);
    println!("   Transition ID: {}", t2.id);
    
    // Check conversation state
    println!("\n4. Conversation state:");
    println!("   Total transitions: {}", conversation.history().len());
    println!("   Session IDs: {:?}", conversation.session_ids());
    println!("   Total cost: ${}", conversation.total_cost());
    
    // Note: tool extraction from conversations doesn't work due to cloning issue
    // See LIMITATIONS.md for details
    let tools = conversation.tools_used();
    println!("   Tools used: {:?} (expected empty due to known limitation)", tools);
    
    // Verify transitions are owned by conversation
    assert_eq!(conversation.history().len(), 2);
    assert_eq!(conversation.session_ids().len(), 2);
    
    // Each execution creates a new session ID
    assert_ne!(t1.execution.session_id, t2.execution.session_id);
    
    // But conversation tracks the chain
    assert_eq!(conversation.session_ids()[0], t1.execution.session_id);
    assert_eq!(conversation.session_ids()[1], t2.execution.session_id);
    
    
    println!("\n✅ Conversation V2 test passed!");
}

#[test]
#[ignore]
fn test_multiple_conversations_same_workspace() {
    println!("\n=== Multiple Conversations Test ===\n");
    
    let env = TestEnvironment::setup();
    let workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    
    // Create two conversations in same workspace
    let mut conv1 = Conversation::new(workspace.clone());
    let mut conv2 = Conversation::new(workspace.clone());
    
    println!("1. Created two conversations:");
    println!("   Conv1 ID: {}", conv1.id());
    println!("   Conv2 ID: {}", conv2.id());
    
    // Send messages in each
    println!("\n2. Sending messages...");
    conv1.send("Create conv1.txt with 'First conversation'").unwrap();
    conv2.send("Create conv2.txt with 'Second conversation'").unwrap();
    conv1.send("Add ' continues' to conv1.txt").unwrap();
    
    // Check isolation
    println!("\n3. Checking conversation isolation:");
    println!("   Conv1 transitions: {}", conv1.history().len());
    println!("   Conv2 transitions: {}", conv2.history().len());
    println!("   Conv1 cost: ${}", conv1.total_cost());
    println!("   Conv2 cost: ${}", conv2.total_cost());
    
    // Each conversation maintains its own history
    assert_eq!(conv1.history().len(), 2);
    assert_eq!(conv2.history().len(), 1);
    
    // Different conversation IDs
    assert_ne!(conv1.id(), conv2.id());
    
    println!("\n✅ Multiple conversations test passed!");
}

#[test]
#[ignore]  
fn test_conversation_persistence() {
    println!("\n=== Conversation Persistence Test ===\n");
    
    let env = TestEnvironment::setup();
    let workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    
    let conv_id;
    let save_path = env.workspace.join("conversation.json");
    
    // Create and save conversation
    {
        let mut conv = Conversation::new(workspace.clone());
        conv_id = conv.id();
        
        conv.send("Create a persistent file").unwrap();
        conv.send("Add some content").unwrap();
        
        println!("1. Saving conversation {} to {:?}", conv_id, save_path);
        conv.save(&save_path).unwrap();
    }
    
    // Load conversation
    {
        println!("\n2. Loading conversation from disk...");
        let loaded = Conversation::load(&save_path, workspace).unwrap();
        
        println!("   Loaded ID: {}", loaded.id());
        println!("   Transitions: {}", loaded.history().len());
        println!("   Session IDs: {:?}", loaded.session_ids());
        
        assert_eq!(loaded.id(), conv_id);
        assert_eq!(loaded.history().len(), 2);
    }
    
    println!("\n✅ Persistence test passed!");
}