use claude_sdk::parser::SessionParser;
use claude_sdk::execution::{ClaudePrompt, ClaudeExecution};
use claude_sdk::execution::observer::EnvironmentSnapshot;
use claude_sdk::execution::recorder::Transition;
use uuid::Uuid;
use std::collections::HashMap;
use chrono::Utc;

#[test]
fn test_transition_followup_from_fixtures() {
    let before_path = "tests/fixtures/transitions/before_example.jsonl";
    let after_path = "tests/fixtures/transitions/after_example.jsonl";

    let before_session = SessionParser::new(before_path).parse().expect("parse before");
    let after_session = SessionParser::new(after_path).parse().expect("parse after");

    let before_snap = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: before_path.into(),
        session_id: Some(before_session.session_id.clone()),
        timestamp: Utc::now(),
        session: Some(std::sync::Arc::new(before_session)),
    };
    let after_snap = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: after_path.into(),
        session_id: Some(after_session.session_id.clone()),
        timestamp: Utc::now(),
        session: Some(std::sync::Arc::new(after_session)),
    };

    let prompt = ClaudePrompt { text: "followup".to_string(), continue_session: true, resume_session_id: None };
    let exec = ClaudeExecution { prompt: prompt.clone(), response: "ok".to_string(), session_id: "sess1".to_string(), cost: 0.0, duration_ms: 0, model: "test".to_string(), timestamp: Utc::now() };

    let transition = Transition {
        id: Uuid::new_v4(),
        before: before_snap,
        prompt,
        execution: exec,
        after: after_snap,
        recorded_at: Utc::now(),
        metadata: serde_json::Value::Null,
    };

    let new_msgs = transition.new_messages();
    assert_eq!(new_msgs.len(), 1);
    assert!(new_msgs[0].is_assistant_message());
    assert!(transition.tool_executions().is_empty());
}
