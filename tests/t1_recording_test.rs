mod common;
use claude_sdk::execution::{Conversation, Workspace};
use common::TestEnvironment;
use std::sync::Arc;

#[test]
#[ignore]
fn test_recording_after_load() {
    let env = TestEnvironment::setup();
    let workspace = Arc::new(Workspace::new(env.workspace.clone()).unwrap());
    let save_path = env.workspace.join("recording.json");

    {
        let mut conv = Conversation::new_with_options(workspace.clone(), true).unwrap();
        conv.send("Create a file called foo.txt with 'hello'")
            .unwrap();
        conv.save(&save_path).unwrap();
    }

    let mut conv = Conversation::load(&save_path, workspace.clone(), true).unwrap();
    conv.send("Append ' world' to foo.txt").unwrap();

    let recorder = conv.recorder().expect("recorder missing");
    let recent = recorder.recent(Some(1)).unwrap();
    assert_eq!(recent.len(), 1);
}
