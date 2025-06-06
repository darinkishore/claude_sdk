# Claude SDK Self-Programming Demo

This demonstrates the meta-programming capability of the Claude SDK - Claude using the SDK to implement features in the SDK itself!

## What This Demo Does

The `self_improve.py` script showcases Claude:
1. Loading the Claude SDK project as a workspace
2. Using the SDK's own API to send a prompt to itself
3. Implementing a new feature (configurable model selection)
4. Committing the changes to the repository

## The Feature Implemented

Claude successfully added configurable model selection to the SDK:
- Previously, the model was hardcoded to `claude-sonnet-4-20250514`
- Now users can specify which model to use via the API
- The implementation touched 5 files across Rust and Python

## Running the Demo

```bash
# Build the SDK first
uv build

# Install the SDK
uv pip install dist/claude_sdk-*.whl

# Run the self-improvement script
uv run python self_improve.py
```

## Testing the Feature

Two test scripts are provided:

1. **test_model_config.py** - Basic API test (verifies the API accepts model parameter)
2. **test_model_integration.py** - Full integration test (actually executes Claude with different models)

Valid test models:
- `claude-3-7-sonnet-20250219`
- `claude-sonnet-4-20250514` (default)

## Lessons Learned

1. **Prompt Specificity Matters**: The initial implementation only added model config at the Workspace level, not Conversation level. More specific requirements would have yielded better results.

2. **Integration Testing is Crucial**: Testing that the API accepts a parameter is different from testing that it works end-to-end.

3. **Self-Programming Works**: The SDK successfully modified itself, demonstrating the potential for AI systems to improve their own code.

## Cost and Performance

- **Cost**: $1.81 for the self-improvement execution
- **Duration**: ~6.6 minutes
- **Files Modified**: 5 core files
- **Success**: Feature works as intended

## Future Improvements

See TODO.md for ideas on improving the self-programming capability, including:
- Better prompt specification
- More comprehensive integration tests
- Model configuration at multiple API levels