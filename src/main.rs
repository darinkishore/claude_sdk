use rust_sdk::{SessionParser, ClaudeError};
use std::env;

fn main() -> Result<(), ClaudeError> {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <session.jsonl>", args[0]);
        eprintln!("\nExample: {} /path/to/session_20240101_120000.jsonl", args[0]);
        std::process::exit(1);
    }
    
    let file_path = &args[1];
    
    println!("Parsing session file: {}", file_path);
    println!("{}", "=".repeat(50));
    
    let parser = SessionParser::new(file_path);
    let session = parser.parse()?;
    
    println!("Session ID: {}", session.session_id);
    println!("Total messages: {}", session.metadata.total_messages);
    println!("  User messages: {}", session.metadata.user_messages);
    println!("  Assistant messages: {}", session.metadata.assistant_messages);
    println!();
    
    println!("Cost: ${:.6}", session.metadata.total_cost_usd);
    println!("Duration: {}ms", session.metadata.total_duration_ms);
    println!();
    
    if let Some(first_ts) = session.metadata.first_message_timestamp {
        println!("First message: {}", first_ts);
    }
    if let Some(last_ts) = session.metadata.last_message_timestamp {
        println!("Last message: {}", last_ts);
    }
    println!();
    
    println!("Conversation tree stats:");
    let stats = session.conversation_tree.stats();
    println!("  Max depth: {}", stats.max_depth);
    println!("  Branches: {}", stats.num_branches);
    println!("  Leaf nodes: {}", stats.leaf_count);
    println!();
    
    if !session.metadata.unique_tools_used.is_empty() {
        println!("Tools used:");
        for tool in &session.metadata.unique_tools_used {
            println!("  - {}", tool);
        }
        println!("Total tool calls: {}", session.metadata.total_tool_calls);
    }
    
    Ok(())
}