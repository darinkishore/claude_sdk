# Directory: src/conversation

This module reconstructs threaded conversations from parsed Claude sessions. `ConversationTree` builds a hierarchy of messages using parent UUIDs, tracks orphaned or circular references, and exposes traversal helpers for analysis.

Key files:
- `tree.rs` defines `ConversationTree` and `ConversationNode`. Methods like `all_messages`, `leaf_nodes`, `path_to_message`, and `stats` help inspect the structure.
- `mod.rs` re-exports the tree types for the rest of the crate.
