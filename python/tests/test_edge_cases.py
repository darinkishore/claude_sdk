import pytest
from pathlib import Path
import claude_code_analytics

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MALFORMED = FIXTURES_DIR / "malformed.jsonl"
LARGE_SESSION = Path(__file__).resolve().parents[2] / "tests" / "db68d083-0471-4213-8609-356b0bf38fec.jsonl"


def test_malformed_jsonl_raises_parse_error():
    with pytest.raises(claude_code_analytics.ParseError):
        claude_code_analytics.load(MALFORMED)


def test_large_session_loads():
    session = claude_code_analytics.load(LARGE_SESSION)
    assert len(session.messages) > 0
