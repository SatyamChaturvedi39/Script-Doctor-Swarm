import asyncio, os, sys
from dotenv import load_dotenv
load_dotenv('../.env')

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from langchain_core.messages import HumanMessage, SystemMessage

async def test():
    llm = get_llm(temperature=0.1)
    messages = [
        SystemMessage(content="Return ONLY valid JSON. No other text."),
        HumanMessage(content='Return this exact JSON: {"status": "ok", "model": "working"}'),
    ]
    raw = await invoke_llm_with_retry(llm, messages)
    print("Raw type:", type(raw).__name__)
    print("Raw[:80]:", repr(raw[:80]))
    parsed = parse_json_from_response(raw)
    print("Parsed:", parsed)
    assert parsed.get("status") == "ok", f"Unexpected: {parsed}"
    print("PASS: response is str, JSON parsed correctly")

asyncio.run(test())
