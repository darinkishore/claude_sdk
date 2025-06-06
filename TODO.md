# TODO

## T1 - Execution Engine

- [x] Make model configurable in ClaudeExecutor (currently hardcoded to claude-sonnet-4-20250514)
  - Add model field to ClaudeExecutor struct
  - Add set_model() method
  - Pass model flag only if explicitly set
  - Consider making it configurable via environment variable

## API Improvements

- [ ] Refactor ClaudePrompt to remove redundant continue_session flag
  - Use only resume_session_id where None = new session, Some(id) = continue
- [ ] Remove project name inference logic
  - Always work with explicit filesystem paths
- [ ] Fix remaining integration tests to work with new API structure

## Python Bindings

- [x] Expose model configuration in Python API
- [ ] Add workspace settings configuration (skip_permissions, etc.)