use claude_sdk::execution::{Conversation, ConversationMetadata, Workspace, ClaudeExecution, ClaudePrompt, EnvironmentSnapshot, Transition};
use claude_sdk::parser::SessionParser;
use std::collections::HashMap;
use std::sync::Arc;
use tempfile::TempDir;
use uuid::Uuid;
use chrono::Utc;
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;

#[test]
fn test_conversation_tools_used() {
    // Create temporary workspace and fake claude binary
    let tmp_workspace = TempDir::new().unwrap();
    let fake_bin_dir = TempDir::new().unwrap();
    let fake_claude = fake_bin_dir.path().join("claude");
    fs::write(&fake_claude, "#!/bin/sh\nexit 1").unwrap();
    let mut perms = fs::metadata(&fake_claude).unwrap().permissions();
    perms.set_mode(0o755);
    fs::set_permissions(&fake_claude, perms).unwrap();
    // Prepend fake bin to PATH so which::which finds it
    let old_path = std::env::var("PATH").unwrap_or_default();
    let new_path = format!("{}:{}", fake_bin_dir.path().display(), old_path);
    std::env::set_var("PATH", &new_path);

    let workspace = Arc::new(Workspace::new(tmp_workspace.path().to_path_buf()).unwrap());

    let session_path = PathBuf::from("tests/fixtures/example_sample.jsonl");
    let parser = SessionParser::new(&session_path);
    let session = parser.parse().unwrap();
    let mut tools = session.metadata.unique_tools_used.clone();
    tools.sort();

    let snapshot = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: session_path.clone(),
        timestamp: Utc::now(),
        session: Some(session),
    };

    let execution = ClaudeExecution {
        prompt: ClaudePrompt::default(),
        response: String::new(),
        session_id: "sess1".to_string(),
        cost: 0.0,
        duration_ms: 0,
        tool_calls: tools.clone(),
        model: "test".to_string(),
        timestamp: Utc::now(),
    };

    let transition = Transition {
        id: Uuid::new_v4(),
        before: snapshot.clone(),
        prompt: ClaudePrompt::default(),
        execution,
        after: snapshot,
        recorded_at: Utc::now(),
        metadata: serde_json::Value::Null,
    };

    // Build conversation JSON
    let meta = ConversationMetadata {
        created_at: Utc::now(),
        workspace_path: tmp_workspace.path().to_path_buf(),
        total_cost_usd: 0.0,
        total_messages: 1,
    };
    let conv_json = serde_json::json!({
        "id": Uuid::new_v4(),
        "transitions": [transition],
        "session_ids": ["sess1"],
        "metadata": meta,
    });

    let conv_path = tmp_workspace.path().join("conv.json");
    fs::write(&conv_path, serde_json::to_string(&conv_json).unwrap()).unwrap();

    let conv = Conversation::load(&conv_path, workspace).unwrap();
    assert_eq!(conv.tools_used(), tools);

    // restore PATH
    std::env::set_var("PATH", old_path);
}
