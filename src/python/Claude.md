# Directory: src/python

Bindings that expose the Rust library to Python via PyO3. The `claude_sdk` Python package is built from these files.

- `mod.rs` registers the module and pulls in all classes/functions.
- `classes.rs` defines Python-visible wrappers for Rust types such as `Message`, `Session`, and `Project`.
- `execution.rs` exposes `Workspace` and `Conversation` to Python, allowing scripts to drive the CLI programmatically.
- `functions.rs` provides convenience helpers like `load` or `find_sessions` that return parsed data structures.
- `models.rs` mirrors the Rust data models so they can be serialized/deserialized in Python.
- `exceptions.rs` creates Python exception types for error handling.
- `utils.rs` converts `serde_json::Value` into native Python objects.
