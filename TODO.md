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
- [ ] Add model configuration at Conversation level (not just Workspace)
  - Currently model can only be set at Workspace/Agent level
  - Should be able to change model mid-conversation

## Python Bindings

- [x] Expose model configuration in Python API
- [ ] Add workspace settings configuration (skip_permissions, etc.)

## Self-Programming Improvements

- [ ] Better prompt specification for self-improvement tasks
  - Be more explicit about API design requirements
  - Specify all levels where configuration should be available
- [ ] Add integration tests for self-implemented features
  - Test with actual Claude CLI execution
  - Verify model parameter is passed correctly
  - Valid test models: claude-3-7-sonnet-20250219, claude-sonnet-4-20250514