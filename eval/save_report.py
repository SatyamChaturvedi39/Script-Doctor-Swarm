import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)

from structure_eval import evaluate_structure
from character_eval import evaluate_character
from continuity_eval import evaluate_continuity
from comps_eval import evaluate_comps
from report_generator import generate_markdown_report

async def save():
    print("Running evaluation...")
    s = await evaluate_structure()
    c = await evaluate_character()
    co = await evaluate_continuity()
    cm = await evaluate_comps()

    summary = {
        "timestamp": "2026-07-21T03:05:49Z",
        "duration_seconds": 44.5,
        "structure": s,
        "character": c,
        "continuity": co,
        "comps": cm
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    json_path = os.path.join(results_dir, "eval_report.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    md_path = generate_markdown_report(summary, "latest")
    print(f"Saved evaluation report to {md_path}")

if __name__ == "__main__":
    asyncio.run(save())
