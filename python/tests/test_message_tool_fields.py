import claude_sdk
from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


@pytest.mark.parametrize("path", sorted(FIXTURES_DIR.rglob("*.jsonl")))
def test_tool_fields_present(path: Path):
    session = claude_sdk.load(path)
    # ensure we have text for every message
    assert all(m.text for m in session.messages)
    # at least one tool use or result should be present in the fixture
    assert any(m.tool_uses for m in session.messages) or any(
        m.tool_results for m in session.messages
    )

