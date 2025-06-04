use claude_sdk::execution::{observer::{EnvironmentSnapshot, PRE_CONVERSATION_SESSION_ID, NO_SESSION_FILE}};
use std::collections::HashMap;
use std::path::PathBuf;

#[test]
fn test_first_snapshot_serialization_roundtrip() {
    // create a snapshot representing the first turn
    let snap = EnvironmentSnapshot {
        files: HashMap::new(),
        session_file: PathBuf::from(NO_SESSION_FILE),
        session_id: Some(PRE_CONVERSATION_SESSION_ID.to_string()),
        timestamp: chrono::Utc::now(),
        session: None,
    };

    // serialize and deserialize
    let json = serde_json::to_string(&snap).expect("serialize");
    let deser: EnvironmentSnapshot = serde_json::from_str(&json).expect("deserialize");

    assert_eq!(deser.session_id.unwrap(), PRE_CONVERSATION_SESSION_ID);
    assert_eq!(deser.session_file, PathBuf::from(NO_SESSION_FILE));
}
