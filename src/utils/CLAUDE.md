# Directory: src/utils

Helper functions for path handling, project discovery, and analyzing session data.

- `path.rs` converts between filesystem paths and Claude's encoded project names.
- `discovery.rs` walks directories to find Claude projects or session files.
- `analysis.rs` provides utilities like `analyze_tool_patterns` and `calculate_session_metrics` for inspecting execution logs.
- `mod.rs` re-exports these helper modules.
