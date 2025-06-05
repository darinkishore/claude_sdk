# Directory: tests/fixtures

Contains sample session files used by unit and integration tests.

- `example_sample.jsonl` is a trimmed session used by parser unit tests.
- `transitions/` holds before/after snapshots derived from `example_sample.jsonl` using `scripts/update_transition_fixtures.sh`.
- `sessions/` holds short real-world logs that allow the integration tests to run without requiring a full Claude install.
