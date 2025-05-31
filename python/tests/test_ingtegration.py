import json
from pathlib import Path
import claude_sdk

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "example_sample.jsonl"

def test_fixture_parsing():
    session = claude_sdk.load(FIXTURE)
    with open(FIXTURE) as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(session.messages) == len(records)

    for msg, raw in zip(session.messages, records):
        assert msg.uuid == raw["uuid"]
        assert msg.parent_uuid == raw.get("parentUuid")
        assert msg.is_sidechain == raw["isSidechain"]
        assert msg.cwd == raw["cwd"]
        assert msg.role == raw["message"]["role"]
        assert msg.model == raw["message"]["model"]
        assert msg.cost == raw["costUSD"]
        if raw["message"]["stop_reason"]:
            assert msg.stop_reason == raw["message"]["stop_reason"]
        else:
            assert msg.stop_reason is None
        if raw["message"]["usage"]:
            usage = msg.usage
            assert usage.input_tokens == raw["message"]["usage"]["input_tokens"]
            assert usage.output_tokens == raw["message"]["usage"]["output_tokens"]
            assert usage.service_tier == raw["message"]["usage"]["service_tier"]
        else:
            assert msg.usage is None

        blocks = msg.get_content_blocks()
        assert len(blocks) == len(raw["message"]["content"])
        for b, r in zip(blocks, raw["message"]["content"]):
            if r["type"] == "text":
                assert isinstance(b, claude_sdk.TextBlock)
                assert b.text == r["text"]
            elif r["type"] == "thinking":
                assert isinstance(b, claude_sdk.ThinkingBlock)
                assert b.thinking == r["thinking"]
                assert b.signature == r["signature"]
            elif r["type"] == "tool_use":
                assert isinstance(b, claude_sdk.ToolUseBlock)
                assert b.id == r["id"]
                assert b.name == r["name"]
            elif r["type"] == "tool_result":
                assert isinstance(b, claude_sdk.ToolResultBlock)
                assert b.tool_use_id == r["tool_use_id"]
                assert b.content == r["content"]
                assert b.is_error == r["is_error"]
            elif r["type"] == "image":
                assert isinstance(b, claude_sdk.ImageBlock)
                assert b.media_type == r["source"]["media_type"]
                assert b.source_type == r["source"]["type"]
                assert b.data == r["source"]["data"]
        
    # ensure round trip
    assert session.total_cost == sum(r["costUSD"] for r in records)
