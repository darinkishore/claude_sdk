use claude_sdk::SessionParser;
use std::thread;

#[test]
fn test_problematic_file() {
    // Run with larger stack size
    let child = thread::Builder::new()
        .stack_size(8 * 1024 * 1024) // 8MB stack
        .spawn(|| {
            test_with_large_stack();
        })
        .unwrap();
        
    child.join().unwrap();
}

fn test_with_large_stack() {
    let file_path = "/Users/darin/.claude/projects/-Users-darin-Projects-apply-model/e4803ec5-5f6a-4214-bcef-daeb844c4ee2.jsonl";
    
    println!("Parsing problematic file: {}", file_path);
    
    let parser = SessionParser::new(file_path);
    println!("Starting parse...");
    match parser.parse() {
        Ok(session) => {
            println!("Parse succeeded! Messages: {}", session.messages.len());
            println!("Orphaned: {:?}", session.conversation_tree.orphaned_messages.len());
            println!("Circular: {:?}", session.conversation_tree.circular_references.len());
            println!("Root messages: {}", session.conversation_tree.root_messages.len());
            
            // Don't call stats() which might trigger the recursion
            // println!("Stats: {:?}", session.conversation_tree.stats());
        }
        Err(e) => {
            println!("Error: {}", e);
        }
    }
}