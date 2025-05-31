use rust_sdk::SessionParser;

#[test]
fn test_single_file() {
    // Test a specific file that might be causing issues
    let file_path = "/Users/darin/.claude/projects/-Users-darin-Projects-apply-model/482455c4-5285-4efd-a98a-a6d3261e0d94.jsonl";
    
    println!("Parsing file: {}", file_path);
    
    let parser = SessionParser::new(file_path);
    match parser.parse() {
        Ok(session) => {
            println!("Success! Messages: {}", session.messages.len());
            println!("Orphaned: {:?}", session.conversation_tree.orphaned_messages.len());
            println!("Circular: {:?}", session.conversation_tree.circular_references.len());
        }
        Err(e) => {
            println!("Error: {}", e);
        }
    }
}