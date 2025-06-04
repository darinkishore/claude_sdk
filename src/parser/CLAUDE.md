# Directory: src/parser

Rust parser for Claude's line oriented JSONL session logs.

- `session.rs` implements `SessionParser`. It validates each JSON record, builds `ParsedSession` with a conversation tree and metadata, and provides helpers like `records_iter`, `extract_tool_usage`, `discover_sessions`, and `session_info` for quick scans.
- `mod.rs` re-exports the parser so other crates can create `SessionParser` instances.
