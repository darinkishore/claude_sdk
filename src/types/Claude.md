# Directory: src/types

Core data models used throughout the SDK and exposed to Python.

- `message.rs` defines `MessageRecord` along with the nested `ContentBlock` variants.
- `content.rs` describes each block type including text, tool calls, and tool results.
- `session.rs` groups messages into a `ParsedSession` with a `ConversationTree` and metadata.
- `metadata.rs` computes analytics like unique tools used and token counts for a session.
- `tool.rs` records individual tool executions and helper methods for durations and success flags.
- `project.rs` models a Claude project discovered on disk.
- `enums.rs` holds enums for message roles and content kinds.
- `mod.rs` re-exports these types for easy access.
