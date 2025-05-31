# Python SDK to Rust SDK Migration Plan

## Objective
Replace the Python claude-sdk with a Rust implementation that provides identical Python bindings via PyO3, ensuring seamless migration for existing users.

## Current State (as of migration start)
- **Python SDK**: Complete implementation in `py_sdk/` with full API
- **Rust SDK**: Core implementation complete, Python bindings partially implemented
- **Missing**: Complete Python API parity in Rust bindings

## Migration Strategy

### Phase 1: API Parity (HIGH PRIORITY)
1. **Type Stub File (.pyi)**
   - Update `python/claude_sdk/_core.pyi` with all exported types
   - Include all classes, functions, and exceptions
   - Ensure proper type hints for IDE support

2. **Session Class** ✓ (Completed by first subagent)
   - All properties: session_id, messages, metadata, total_cost, tools_used, duration, etc.
   - All methods: get_messages_by_role(), filter_messages(), get_conversation_tree(), etc.
   - Magic methods: __len__(), __iter__(), __repr__(), __str__()

3. **Message Class**
   - Properties: role, text, cost, tools, timestamp, uuid, parent_uuid, is_sidechain, cwd
   - Methods: get_tool_blocks(), get_text_blocks(), has_tool_use()
   - Content block access methods
   - Proper __repr__() and __str__()

4. **Project Class**
   - Properties: name, path, sessions, total_cost, total_messages
   - Methods: get_session(), filter_sessions(), get_all_messages()
   - Cost aggregation methods
   - Session management

### Phase 2: Supporting Infrastructure
5. **Utility Functions**
   - Ensure find_sessions() works identically
   - Ensure find_projects() works identically
   - Ensure load() and load_project() work identically

6. **Exception Hierarchy**
   - ClaudeSDKError (base)
   - ParseError
   - ValidationError
   - SessionError

7. **Model Classes**
   - Ensure all Pydantic models have PyO3 equivalents
   - SessionMetadata, ToolResult, ToolExecution, etc.

### Phase 3: Quality Assurance
8. **Documentation**
   - Comprehensive docstrings on all classes/methods
   - Examples in docstrings
   - Migration guide for users

9. **Testing**
   - Port key tests from Python SDK
   - Ensure behavior matches exactly
   - Performance benchmarks

10. **Package Configuration**
    - Update pyproject.toml
    - Ensure maturin builds correctly
    - Set up proper versioning

## Implementation Guidelines
- **Exact API Match**: Every public method/property must match Python SDK
- **Performance**: Leverage Rust's speed while maintaining Python compatibility
- **Error Handling**: Map Rust errors to appropriate Python exceptions
- **Memory Safety**: Handle Rust ownership properly with cloning where needed
- **Type Conversions**: Ensure seamless Rust<->Python type conversions

## Success Criteria
1. All existing Python SDK examples run unchanged with Rust SDK
2. All public APIs have identical signatures
3. Performance is equal or better than Python SDK
4. Zero breaking changes for users

## Git Commit Strategy
- Each class completion gets its own commit
- Clear commit messages explaining what was implemented
- No force pushes or hard resets
- Preserve full history for audit trail

## Current Progress Tracking
See TodoRead for real-time status of each task.