"""
Quick analysis of what's in our test fixture to ensure we have good test data.
"""
import json
from pathlib import Path
from collections import Counter

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "sessions"
    / "swe_fixer_download_debug.jsonl"
)

def analyze_fixture():
    with open(FIXTURE_PATH) as f:
        records = [json.loads(line) for line in f if line.strip()]
    
    print(f"Total messages: {len(records)}")
    
    # Analyze roles
    roles = Counter(r['message']['role'] for r in records if r.get('message'))
    print(f"\nRoles: {dict(roles)}")
    
    # Analyze tools
    tools_used = []
    for r in records:
        if r.get('message', {}).get('content'):
            for content in r['message']['content']:
                if isinstance(content, dict) and content.get('type') == 'tool_use':
                    tools_used.append(content.get('name'))
    
    tool_counts = Counter(tools_used)
    print(f"\nTools used: {dict(tool_counts)}")
    print(f"Total tool uses: {sum(tool_counts.values())}")
    
    # Check token usage
    messages_with_tokens = sum(1 for r in records if r.get('message', {}).get('usage'))
    print(f"\nMessages with token info: {messages_with_tokens}")
    
    # Sample token data
    for r in records:
        if r.get('message', {}).get('usage'):
            usage = r['message']['usage']
            print(f"  Sample token data: input={usage.get('input_tokens')}, output={usage.get('output_tokens')}")
            break
    
    # Check stop reasons
    stop_reasons = Counter(r['message'].get('stop_reason') for r in records 
                          if r.get('message', {}).get('stop_reason'))
    print(f"\nStop reasons: {dict(stop_reasons)}")
    
    # Check sidechains
    sidechains = sum(1 for r in records if r.get('isSidechain'))
    print(f"\nMessages in sidechains: {sidechains}")
    
    # Check threading
    with_parent = sum(1 for r in records if r.get('parentUuid'))
    print(f"\nMessages with parent: {with_parent}")
    print(f"Root messages: {len(records) - with_parent}")
    
    # Check costs
    with_cost = sum(1 for r in records if r.get('costUSD', 0) > 0)
    print(f"\nMessages with cost: {with_cost}")
    
    # Check thinking blocks
    thinking_messages = 0
    for r in records:
        if r.get('message', {}).get('content'):
            for content in r['message']['content']:
                if isinstance(content, dict) and content.get('type') == 'thinking':
                    thinking_messages += 1
                    break
    print(f"\nMessages with thinking blocks: {thinking_messages}")

if __name__ == "__main__":
    analyze_fixture()