"""
Script Doctor Swarm — Comprehensive Evaluation Runner.

Runs:
  - Structure evaluation (reference films)
  - Character evaluation (canary script)
  - Continuity evaluation (canary script)
  - Comps evaluation (reference films)

Features:
  - Persistent caching (`eval_cache.json`): skips already completed test cases to save API quota.
  - `--force` flag: forces a full re-evaluation from scratch.
  - Pacing delay (`--delay`): adds fixed pause between API calls to prevent 429 rate limits.
  - `--dry-run` flag: runs a small 1-case dry run to verify cache resume behavior.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Load env variables (required for Gemini/TMDB API keys during eval)
load_dotenv()

# Setup root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("script_doctor.eval.runner")

# Add backend directory to path so we can import agents
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)

from character_eval import evaluate_character
from comps_eval import evaluate_comps
from continuity_eval import evaluate_continuity
from eval_cache import clear_cache, load_cache
from report_generator import generate_markdown_report
from structure_eval import evaluate_structure


def save_intermediate_report(summary: dict) -> None:
    """Save latest evaluation summary JSON and Markdown immediately."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    latest_json_path = os.path.join(results_dir, "eval_report_latest.json")
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    try:
        generate_markdown_report(summary, "latest")
    except Exception as e:
        logger.warning("Could not generate intermediate markdown report: %s", e)


async def run_full_evaluation(
    force: bool = False,
    delay_seconds: float = 3.0,
    dry_run: bool = False,
):
    logger.info("==================================================")
    logger.info("   Starting Script Doctor Swarm Evaluation Run    ")
    if force:
        logger.info("   Mode: FORCE (ignoring existing cached results) ")
    else:
        logger.info("   Mode: CACHED (skipping already completed cases)")
    if dry_run:
        logger.info("   Mode: DRY RUN (running 1 test case to test cache)")
    logger.info("   API Pacing Delay: %.1fs", delay_seconds)
    logger.info("==================================================")

    # Check for API keys unless in dry-run with full cache
    from config import get_settings

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        logger.error(
            "CRITICAL: GEMINI_API_KEY environment variable is empty. Evaluation will fail."
        )
        return
    if not settings.TMDB_API_KEY:
        logger.error(
            "CRITICAL: TMDB_API_KEY environment variable is empty. Comps evaluation will fail."
        )
        return

    start_time = datetime.now()

    films = ["get_out"] if dry_run else ["get_out", "whiplash", "parasite"]

    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "duration_seconds": 0.0,
        "structure": [],
        "character": {},
        "continuity": {},
        "comps": [],
    }

    # 1. Structure Evaluation
    logger.info("--- Starting Structure Evaluation ---")
    summary["structure"] = await evaluate_structure(
        force=force, delay_seconds=delay_seconds, films=films
    )
    save_intermediate_report(summary)

    if dry_run:
        logger.info("Dry run complete (Structure test case evaluated/skipped).")
        end_time = datetime.now()
        summary["duration_seconds"] = round((end_time - start_time).total_seconds(), 1)
        save_intermediate_report(summary)
        return

    # 2. Character Evaluation
    logger.info("--- Starting Character Evaluation ---")
    summary["character"] = await evaluate_character(
        force=force, delay_seconds=delay_seconds, script_name="canary_02"
    )
    save_intermediate_report(summary)

    # 3. Continuity Evaluation
    logger.info("--- Starting Continuity Evaluation ---")
    summary["continuity"] = await evaluate_continuity(
        force=force, delay_seconds=delay_seconds, script_name="canary_02"
    )
    save_intermediate_report(summary)

    # 4. Comps Evaluation
    logger.info("--- Starting Comps Evaluation ---")
    summary["comps"] = await evaluate_comps(
        force=force, delay_seconds=delay_seconds, films=films
    )

    end_time = datetime.now()
    summary["duration_seconds"] = round((end_time - start_time).total_seconds(), 1)

    # Save final report with timestamp
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    report_json_path = os.path.join(results_dir, f"eval_report_{timestamp_str}.json")

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    save_intermediate_report(summary)

    logger.info("Evaluation results saved to JSON: %s", report_json_path)
    logger.info("==================================================")
    logger.info("           Evaluation Swarm Complete              ")
    logger.info("==================================================")


def main():
    parser = argparse.ArgumentParser(
        description="Script Doctor Swarm — Evaluation Runner"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full evaluation, ignoring cached results",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Pacing delay in seconds between API calls (default: 3.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run a 1-test-case dry run to verify caching behavior",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the eval_cache.json file before running",
    )

    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    asyncio.run(
        run_full_evaluation(
            force=args.force,
            delay_seconds=args.delay,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
