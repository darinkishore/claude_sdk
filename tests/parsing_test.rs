use rust_sdk::{SessionParser, MessageRecord, ContentBlock, Role};
use std::io::Write;
use tempfile::NamedTempFile;

#[test]
fn test_parse_simple_session() {
    // Create a temporary JSONL file with test data
    let mut temp_file = NamedTempFile::new().unwrap();
    
    // Write test JSONL data
    let test_data = r#"{"parent_uuid":null,"is_sidechain":false,"user_type":"human","cwd":"/home/user/project","session_id":"session_123","version":"1.0.0","message_type":"user","message":{"id":"msg_1","role":"user","model":null,"content":[{"type":"text","text":"Hello, Claude!"}],"stop_reason":null,"usage":null},"cost_usd":0.0,"duration_ms":10,"request_id":"req_1","uuid":"00000000-0000-0000-0000-000000000001","timestamp":"2024-01-01T00:00:00Z"}
{"parent_uuid":"00000000-0000-0000-0000-000000000001","is_sidechain":false,"user_type":"system","cwd":"/home/user/project","session_id":"session_123","version":"1.0.0","message_type":"assistant","message":{"id":"msg_2","role":"assistant","model":"claude-3-opus-20240229","content":[{"type":"text","text":"Hello! How can I help you today?"}],"stop_reason":"end_turn","usage":{"input_tokens":10,"cache_creation_input_tokens":null,"cache_read_input_tokens":null,"output_tokens":8,"service_tier":"default"}},"cost_usd":0.001,"duration_ms":500,"request_id":"req_2","uuid":"00000000-0000-0000-0000-000000000002","timestamp":"2024-01-01T00:00:01Z"}"#;
    
    writeln!(temp_file, "{}", test_data).unwrap();
    temp_file.flush().unwrap();
    
    // Parse the session
    let parser = SessionParser::new(temp_file.path());
    let session = parser.parse().unwrap();
    
    // Verify basic properties
    assert_eq!(session.session_id, "session_123");
    assert_eq!(session.messages.len(), 2);
    
    // Check first message
    let first_msg = &session.messages[0];
    assert!(first_msg.is_user_message());
    assert_eq!(first_msg.message.content.len(), 1);
    if let ContentBlock::Text { text } = &first_msg.message.content[0] {
        assert_eq!(text, "Hello, Claude!");
    } else {
        panic!("Expected text content block");
    }
    
    // Check second message
    let second_msg = &session.messages[1];
    assert!(second_msg.is_assistant_message());
    assert_eq!(second_msg.cost(), 0.001);
    assert_eq!(second_msg.duration(), 500);
    
    // Check conversation tree
    assert_eq!(session.conversation_tree.root_messages.len(), 1);
    let stats = session.conversation_tree.stats();
    assert_eq!(stats.total_messages, 2);
    assert_eq!(stats.max_depth, 2);
    assert_eq!(stats.num_branches, 0);
    assert_eq!(stats.leaf_count, 1);
    
    // Check metadata
    assert_eq!(session.metadata.total_messages, 2);
    assert_eq!(session.metadata.user_messages, 1);
    assert_eq!(session.metadata.assistant_messages, 1);
    assert_eq!(session.metadata.total_cost_usd, 0.001);
    assert_eq!(session.metadata.total_duration_ms, 510);
}

#[test]
fn test_parse_tool_usage() {
    let mut temp_file = NamedTempFile::new().unwrap();
    
    let test_data = r#"{"parent_uuid":null,"is_sidechain":false,"user_type":"human","cwd":"/home/user","session_id":"session_456","version":"1.0.0","message_type":"user","message":{"id":"msg_1","role":"user","model":null,"content":[{"type":"text","text":"Read the file test.txt"}],"stop_reason":null,"usage":null},"cost_usd":0.0,"duration_ms":10,"request_id":"req_1","uuid":"00000000-0000-0000-0000-000000000003","timestamp":"2024-01-01T00:00:00Z"}
{"parent_uuid":"00000000-0000-0000-0000-000000000003","is_sidechain":false,"user_type":"system","cwd":"/home/user","session_id":"session_456","version":"1.0.0","message_type":"assistant","message":{"id":"msg_2","role":"assistant","model":"claude-3-opus-20240229","content":[{"type":"text","text":"I'll read the file for you."},{"type":"tool_use","id":"tool_1","name":"read_file","input":{"path":"test.txt"}}],"stop_reason":"tool_use","usage":{"input_tokens":15,"cache_creation_input_tokens":null,"cache_read_input_tokens":null,"output_tokens":20,"service_tier":"default"}},"cost_usd":0.002,"duration_ms":300,"request_id":"req_2","uuid":"00000000-0000-0000-0000-000000000004","timestamp":"2024-01-01T00:00:01Z"}
{"parent_uuid":"00000000-0000-0000-0000-000000000004","is_sidechain":false,"user_type":"human","cwd":"/home/user","session_id":"session_456","version":"1.0.0","message_type":"user","message":{"id":"msg_3","role":"user","model":null,"content":[{"type":"tool_result","tool_use_id":"tool_1","content":"File contents: Hello World!","is_error":false}],"stop_reason":null,"usage":null},"cost_usd":0.0,"duration_ms":50,"request_id":"req_3","uuid":"00000000-0000-0000-0000-000000000005","timestamp":"2024-01-01T00:00:02Z"}"#;
    
    writeln!(temp_file, "{}", test_data).unwrap();
    temp_file.flush().unwrap();
    
    let parser = SessionParser::new(temp_file.path());
    let tool_executions = parser.extract_tool_usage().unwrap();
    
    // Verify tool execution
    assert_eq!(tool_executions.len(), 1);
    let exec = &tool_executions[0];
    assert_eq!(exec.tool_name, "read_file");
    assert!(exec.is_success());
    assert_eq!(exec.output.content, "File contents: Hello World!");
    assert_eq!(exec.duration_ms(), 1000); // Time between tool_use and tool_result
}

#[test]
fn test_parse_empty_file() {
    let temp_file = NamedTempFile::new().unwrap();
    let parser = SessionParser::new(temp_file.path());
    
    match parser.parse() {
        Err(rust_sdk::ClaudeError::ParseError(rust_sdk::ParseError::EmptyFile)) => {
            // Expected error
        }
        _ => panic!("Expected EmptyFile error"),
    }
}

#[test]
fn test_conversation_tree_branching() {
    let mut temp_file = NamedTempFile::new().unwrap();
    
    // Create a branching conversation (user edits a message)
    let test_data = r#"{"parent_uuid":null,"is_sidechain":false,"user_type":"human","cwd":"/home/user","session_id":"session_789","version":"1.0.0","message_type":"user","message":{"id":"msg_1","role":"user","model":null,"content":[{"type":"text","text":"First message"}],"stop_reason":null,"usage":null},"cost_usd":0.0,"duration_ms":10,"request_id":"req_1","uuid":"00000000-0000-0000-0000-000000000006","timestamp":"2024-01-01T00:00:00Z"}
{"parent_uuid":"00000000-0000-0000-0000-000000000006","is_sidechain":false,"user_type":"system","cwd":"/home/user","session_id":"session_789","version":"1.0.0","message_type":"assistant","message":{"id":"msg_2","role":"assistant","model":"claude-3-opus-20240229","content":[{"type":"text","text":"Response 1"}],"stop_reason":"end_turn","usage":{"input_tokens":10,"cache_creation_input_tokens":null,"cache_read_input_tokens":null,"output_tokens":5,"service_tier":"default"}},"cost_usd":0.001,"duration_ms":200,"request_id":"req_2","uuid":"00000000-0000-0000-0000-000000000007","timestamp":"2024-01-01T00:00:01Z"}
{"parent_uuid":"00000000-0000-0000-0000-000000000006","is_sidechain":true,"user_type":"system","cwd":"/home/user","session_id":"session_789","version":"1.0.0","message_type":"assistant","message":{"id":"msg_3","role":"assistant","model":"claude-3-opus-20240229","content":[{"type":"text","text":"Alternative response"}],"stop_reason":"end_turn","usage":{"input_tokens":10,"cache_creation_input_tokens":null,"cache_read_input_tokens":null,"output_tokens":5,"service_tier":"default"}},"cost_usd":0.001,"duration_ms":200,"request_id":"req_3","uuid":"00000000-0000-0000-0000-000000000008","timestamp":"2024-01-01T00:00:02Z"}"#;
    
    writeln!(temp_file, "{}", test_data).unwrap();
    temp_file.flush().unwrap();
    
    let parser = SessionParser::new(temp_file.path());
    let session = parser.parse().unwrap();
    
    // Check branching structure
    let stats = session.conversation_tree.stats();
    assert_eq!(stats.total_messages, 3);
    assert_eq!(stats.num_branches, 1); // One branching point
    assert_eq!(stats.leaf_count, 2); // Two leaf nodes
    
    // Check that the root has two children
    let root = &session.conversation_tree.root_messages[0];
    assert_eq!(root.child_count(), 2);
}