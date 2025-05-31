# Claude Code SDK - Rust Implementation

A Rust library for parsing and analyzing Claude Code session data stored in JSONL format.

## Features (T0 - Data Parsing)

- ✅ Parse JSONL session files
- ✅ Build conversation trees with branching support
- ✅ Extract tool usage patterns
- ✅ Calculate session metrics (cost, duration, message counts)
- ✅ Handle compacted sessions with summaries
- ✅ Synchronous API (no async complexity)

## Quick Start

```rust
use rust_sdk::{SessionParser, ClaudeError};

fn main() -> Result<(), ClaudeError> {
    let parser = SessionParser::new("/path/to/session.jsonl");
    let session = parser.parse()?;
    
    println!("Session ID: {}", session.session_id);
    println!("Total messages: {}", session.metadata.total_messages);
    println!("Total cost: ${:.6}", session.metadata.total_cost_usd);
    
    // Access conversation tree
    let stats = session.conversation_tree.stats();
    println!("Max depth: {}", stats.max_depth);
    println!("Branches: {}", stats.num_branches);
    
    Ok(())
}
```

## Usage

### Parse a session file
```bash
cargo run -- /path/to/session_20240101_120000.jsonl
```

### Run tests
```bash
cargo test
```

## Architecture

The SDK follows a clean modular design:

- **types/** - Core data structures (MessageRecord, ContentBlock, etc.)
- **parser/** - JSONL parsing logic
- **conversation/** - Conversation tree reconstruction
- **error.rs** - Error handling
- **utils.rs** - Utility functions

## Integration Tests

The SDK includes comprehensive integration tests that work with real Claude session data:

```bash
# Run all integration tests (requires Claude projects directory)
cargo test -- --ignored

# Run specific integration test
cargo test --test integration_test -- --ignored test_parse_real_sessions
```

Test coverage includes:
- ✅ Parsing real session files (handles camelCase JSONL format)
- ✅ Large file performance (processes 1000+ messages/sec)
- ✅ Tool usage extraction and pattern analysis
- ✅ Session metadata aggregation
- ✅ Conversation branching detection

## Next Steps

- T1: Claude execution capabilities
- T2: Git integration for change tracking
- T3: Real-time session monitoring
- T4: Performance optimizations