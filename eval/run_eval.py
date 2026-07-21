"""
Script Doctor Swarm — Comprehensive Evaluation Runner.

Runs:
  - Structure evaluation (3 reference films)
  - Character evaluation (canary script)
  - Continuity evaluation (canary script)
  - Comps evaluation (3 reference films)

Outputs results to `eval/results/eval_report_<timestamp>.json`
and calls the markdown report generator to produce a human-readable summary.
"""

from __future__ import annotations

import os
import json
import logging
import asyncio
from datetime import datetime

from dotenv import load_dotenv

# Load env variables (required for Gemini/TMDB API keys during eval)
load_dotenv()

# Setup root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("script_doctor.eval.runner")

# Add backend directory to path so we can import agents
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)

from structure_eval import evaluate_structure
from character_eval import evaluate_character
from continuity_eval import evaluate_continuity
from comps_eval import evaluate_comps
from report_generator import generate_markdown_report

async def run_full_evaluation():
    logger.info("==================================================")
    logger.info("   Starting Script Doctor Swarm Evaluation Run    ")
    logger.info("==================================================")
    
    # Check for API keys
    from config import get_settings
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        logger.error("CRITICAL: GEMINI_API_KEY environment variable is empty. Evaluation will fail.")
        return
    if not settings.TMDB_API_KEY:
        logger.error("CRITICAL: TMDB_API_KEY environment variable is empty. Comps evaluation will fail.")
        return
        
    start_time = datetime.now()
    
    # 1. Structure Evaluation
    logger.info("--- Starting Structure Evaluation ---")
    structure_results = await evaluate_structure()
    
    # 2. Character Evaluation
    logger.info("--- Starting Character Evaluation ---")
    character_results = await evaluate_character()
    
    # 3. Continuity Evaluation
    logger.info("--- Starting Continuity Evaluation ---")
    continuity_results = await evaluate_continuity()
    
    # 4. Comps Evaluation
    logger.info("--- Starting Comps Evaluation ---")
    comps_results = await evaluate_comps()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "duration_seconds": round(duration, 1),
        "structure": structure_results,
        "character": character_results,
        "continuity": continuity_results,
        "comps": comps_results
    }
    
    # Save results JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    report_json_path = os.path.join(results_dir, f"eval_report_{timestamp_str}.json")
    
    with open(report_json_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    logger.info("Evaluation results saved to JSON: %s", report_json_path)
    
    # Generate markdown report
    markdown_path = generate_markdown_report(summary, timestamp_str)
    logger.info("Markdown evaluation report generated: %s", markdown_path)
    
    logger.info("==================================================")
    logger.info("           Evaluation Swarm Complete              ")
    logger.info("==================================================")

if __name__ == "__main__":
    asyncio.run(run_full_evaluation())
