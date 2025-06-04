# Directory: src/execution

Core runtime for sending prompts to the Claude CLI and tracking workspace state. These modules power the high level conversation API.

- `executor.rs` defines `ClaudeExecutor`, building command invocations and parsing JSON responses from the CLI. It also handles tool permission flags.
- `observer.rs` produces `EnvironmentSnapshot`s of the workspace and locates session files under `~/.claude/projects`.
- `recorder.rs` stores `Transition` structures to disk so executions can be replayed later.
- `workspace.rs` wires the executor and observer together, exposing methods like `snapshot` and `set_allowed_tools`.
- `conversation.rs` builds on these pieces to manage a multi-turn `Conversation` with its own history of transitions.
- `mod.rs` simply re-exports the public types.
