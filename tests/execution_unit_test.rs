use claude_sdk::execution::{recorder::TransitionRecorder, observer::EnvironmentSnapshot, Transition, ClaudePrompt, ClaudeExecution};
use claude_sdk::types::{MessageRecord, Message, ContentBlock, ToolResultContent, enums::{UserType, MessageType, Role, StopReason}};
use claude_sdk::conversation::ConversationTree;
use claude_sdk::types::metadata::SessionMetadata;
use chrono::Utc;
use serde_json::json;
use std::collections::HashMap;
use std::path::PathBuf;
use tempfile::TempDir;
use uuid::Uuid;

fn sample_transition() -> Transition {
    // Build messages
    let now = Utc::now();
    let uuid1 = Uuid::new_v4();
    let uuid2 = Uuid::new_v4();
    let uuid3 = Uuid::new_v4();

    let msg1 = MessageRecord {
        parent_uuid: None,
        is_sidechain: false,
        user_type: UserType::External,
        cwd: PathBuf::from("/tmp"),
        session_id: "sess1".to_string(),
        version: "1.0".to_string(),
        message_type: MessageType::User,
        message: Message {
            id: Some("m1".to_string()),
            role: Role::User,
            model: None,
            content: vec![ContentBlock::Text { text: "hi".to_string() }],
            stop_reason: None,
            usage: None,
        },
        cost_usd: Some(0.0),
        duration_ms: Some(1),
        request_id: None,
        uuid: uuid1,
        timestamp: now,
        tool_use_result: None,
        is_meta: None,
    };

    let msg2 = MessageRecord {
        parent_uuid: Some(uuid1),
        is_sidechain: false,
        user_type: UserType::Internal,
        cwd: PathBuf::from("/tmp"),
        session_id: "sess1".to_string(),
        version: "1.0".to_string(),
        message_type: MessageType::Assistant,
        message: Message {
            id: Some("m2".to_string()),
            role: Role::Assistant,
            model: None,
            content: vec![
                ContentBlock::Text { text: "reading".to_string() },
                ContentBlock::ToolUse { id: "t1".to_string(), name: "Read".to_string(), input: json!({"path": "file.txt"}) },
            ],
            stop_reason: Some(StopReason::ToolUse),
            usage: None,
        },
        cost_usd: Some(0.0),
        duration_ms: Some(1),
        request_id: None,
        uuid: uuid2,
        timestamp: now + chrono::Duration::milliseconds(1),
        tool_use_result: None,
        is_meta: None,
    };

    let msg3 = MessageRecord {
        parent_uuid: Some(uuid2),
        is_sidechain: false,
        user_type: UserType::External,
        cwd: PathBuf::from("/tmp"),
        session_id: "sess1".to_string(),
        version: "1.0".to_string(),
        message_type: MessageType::User,
        message: Message {
            id: Some("m3".to_string()),
            role: Role::User,
            model: None,
            content: vec![ContentBlock::ToolResult { tool_use_id: "t1".to_string(), content: Some(ToolResultContent::Text("ok".to_string())), is_error: Some(false) }],
            stop_reason: None,
            usage: None,
        },
        cost_usd: Some(0.0),
        duration_ms: Some(1),
        request_id: None,
        uuid: uuid3,
        timestamp: now + chrono::Duration::milliseconds(2),
        tool_use_result: None,
        is_meta: None,
    };

    let before_messages = vec![msg1.clone()];
    let after_messages = vec![msg1.clone(), msg2.clone(), msg3.clone()];

    let before_metadata = SessionMetadata::from_messages(&before_messages, PathBuf::from("before.jsonl"));
    let after_metadata = SessionMetadata::from_messages(&after_messages, PathBuf::from("after.jsonl"));

    let before_session = claude_sdk::types::session::ParsedSession {
        session_id: "sess1".to_string(),
        messages: before_messages,
        summaries: Vec::new(),
        conversation_tree: ConversationTree::from_messages(vec![msg1.clone()]).unwrap(),
        metadata: before_metadata,
    };

    let after_session = claude_sdk::types::session::ParsedSession {
        session_id: "sess1".to_string(),
        messages: after_messages,
        summaries: Vec::new(),
        conversation_tree: ConversationTree::from_messages(vec![msg1, msg2.clone(), msg3.clone()]).unwrap(),
        metadata: after_metadata,
    };

    let before = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: PathBuf::from("before.jsonl"),
        session_id: Some("sess1".to_string()),
        timestamp: now,
        session: Some(before_session.into()),
    };

    let after = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: PathBuf::from("after.jsonl"),
        session_id: Some("sess1".to_string()),
        timestamp: now + chrono::Duration::milliseconds(2),
        session: Some(after_session.into()),
    };

    let prompt = ClaudePrompt { text: "test".to_string(), continue_session: false, resume_session_id: None };
    let execution = ClaudeExecution { prompt: prompt.clone(), response: "done".to_string(), session_id: "sess1".to_string(), cost: 0.0, duration_ms: 1, model: "test".to_string(), timestamp: now };

    Transition {
        id: Uuid::new_v4(),
        before,
        prompt,
        execution,
        after,
        recorded_at: now,
        metadata: serde_json::Value::Null,
    }
}

#[test]
fn test_transition_tool_methods() {
    let transition = sample_transition();
    let new_messages = transition.new_messages();
    assert_eq!(new_messages.len(), 2);
    let execs = transition.tool_executions();
    assert_eq!(execs.len(), 1);
    assert_eq!(execs[0].tool_name, "Read");
    assert!(transition.tools_used().contains(&"Read".to_string()));
    assert!(!transition.has_tool_errors());
}

#[test]
fn test_transition_recorder_roundtrip() {
    let tmp = TempDir::new().unwrap();
    let mut recorder = TransitionRecorder::new(tmp.path()).unwrap();
    let transition = sample_transition();
    let id = transition.id;
    recorder.record(&transition).unwrap();
    let loaded = recorder.load(id).unwrap().unwrap();
    assert_eq!(loaded.id, id);
    let recent = recorder.recent(Some(1)).unwrap();
    assert_eq!(recent.len(), 1);
    assert_eq!(recent[0].id, id);
}

