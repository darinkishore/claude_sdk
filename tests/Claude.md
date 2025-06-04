# Directory: tests

Collection of unit and integration tests for the crate. Many files are prefixed with `t1_` and focus on the execution engine. Most integration tests are ignored by default and require the Claude CLI.

Notable tests:
- `integration/` holds the CLI integration tests.
- `fixtures/` provides sample session logs consumed by various tests.
- `t1_*` files exercise conversation handling, workspace observation, and tool extraction.
