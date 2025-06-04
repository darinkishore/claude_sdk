# Changelog

## [Unreleased]

### What Actually Works
- ✅ Parse Claude session JSONL files
- ✅ Extract messages, tool uses, and costs
- ✅ Find all sessions on your system
- ✅ Control Claude via CLI wrapper
- ✅ Track file changes between commands
- ✅ Python bindings for all core features
- ✅ Cost analysis and reporting

### Known Issues
- 🐛 Tool-only responses show "(no content)"
- 🐛 `--dangerously-skip-permissions` resets after Claude updates
- 🐛 `ClaudeEnvironment.restore()` not implemented
- 🐛 Limited Python test coverage

### Not Yet Implemented
- ❌ DSPy integration modules
- ❌ T2 orchestration layer (ReAct, HTN patterns)
- ❌ Streaming responses
- ❌ Windows support
- ❌ Async API

## [0.1.0] - TBD

Initial release with:
- T0 session parser (complete)
- T1 execution engine (mostly working)
- Basic Python bindings
- Examples and documentation