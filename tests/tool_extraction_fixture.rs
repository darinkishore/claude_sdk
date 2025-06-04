use claude_sdk::SessionParser;
use std::path::PathBuf;

#[test]
fn test_tool_extraction_from_fixture() {
    let path = PathBuf::from("tests/fixtures/sessions/swe_fixer_download_debug.jsonl");
    let parser = SessionParser::new(&path);
    let tool_execs = parser.extract_tool_usage().expect("failed to parse fixture");

    assert!(!tool_execs.is_empty(), "fixture should contain tool executions");
    // Check at least one well-known tool
    let tool_names: Vec<String> = tool_execs.iter().map(|t| t.tool_name.clone()).collect();
    assert!(tool_names.contains(&"Bash".to_string()) || tool_names.contains(&"Edit".to_string()));
}
