use claude_sdk::parser::SessionParser;
use claude_sdk::execution::{ClaudePrompt, ClaudeExecution};
use claude_sdk::execution::observer::{EnvironmentSnapshot};
use claude_sdk::execution::recorder::Transition;
use uuid::Uuid;
use std::collections::HashMap;
use chrono::Utc;
use std::path::Path;

#[test]
fn test_transition_tool_extraction() {
    // Load after fixture representing the first execution
    let after_path = Path::new("tests/fixtures/transitions/after_example.jsonl");
    let parser_after = SessionParser::new(after_path);
    let after_session = parser_after.parse().unwrap();

    // Build snapshots representing the first execution
    let before_snap = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: claude_sdk::execution::observer::NO_SESSION_FILE.into(),
        session_id: Some(claude_sdk::execution::observer::PRE_CONVERSATION_SESSION_ID.to_string()),
        timestamp: Utc::now(),
        session: None,
    };
    let after_snap = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: after_path.to_path_buf(),
        session_id: Some(after_session.session_id.clone()),
        timestamp: Utc::now(),
        session: Some(std::sync::Arc::new(after_session)),
    };

    // Dummy execution info
    let prompt = ClaudePrompt {
        text: "dummy".to_string(),
        continue_session: false,
        resume_session_id: None,
    };
    let exec = ClaudeExecution {
        prompt: prompt.clone(),
        response: "ok".to_string(),
        session_id: "sess1".to_string(),
        cost: 0.0,
        duration_ms: 0,
        model: "test".to_string(),
        timestamp: Utc::now(),
    };

    let transition = Transition {
        id: Uuid::new_v4(),
        before: before_snap,
        prompt,
        execution: exec,
        after: after_snap,
        recorded_at: Utc::now(),
        metadata: serde_json::Value::Null,
    };

    // Validate new messages
    let new_msgs = transition.new_messages();
    assert_eq!(new_msgs.len(), 2);
    assert!(new_msgs[0].is_user_message());
    assert!(new_msgs[1].is_assistant_message());

    // Validate tool extraction
    let tool_execs = transition.tool_executions();
    assert_eq!(tool_execs.len(), 1);
    assert_eq!(tool_execs[0].tool_name, "echo");
    assert!(tool_execs[0].is_success());

    // Helper methods
    assert_eq!(transition.tools_used(), vec!["echo".to_string()]);
    assert!(!transition.has_tool_errors());
}

