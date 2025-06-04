# Directory: tests/common

Utilities shared by multiple tests. `mod.rs` defines `TestEnvironment` which creates a temporary workspace under `~/.claude-sdk/test-environment`. It can discover the corresponding Claude project directory and locate session logs for assertions. The environment cleans up after each test via the `Drop` implementation.
