# Directory: tests/integration

End-to-end tests that execute the real Claude CLI. They are marked `#[ignore]` and must be run manually (`cargo test -- --ignored`).

- `executor_test.rs` exercises `ClaudeExecutor` by running prompts in a temporary workspace.
- `mod.rs` acts as the test harness for additional integration modules.
