"""
Structure Evaluation Module.

Runs the Structure Agent on reference mock scripts and computes the mean absolute percentage
deviation between detected beat positions and ground truth positions.
"""

from __future__ import annotations

import os
import json
import logging
import asyncio

from agents.structure_agent import run_structure_agent
from parser.extractor import estimate_page_count

logger = logging.getLogger("script_doctor.eval.structure")

async def evaluate_structure():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    keys_dir = os.path.join(base_dir, "data", "beat_sheets")
    scripts_dir = os.path.join(base_dir, "data", "canary_scripts")
    
    reference_films = ["get_out", "whiplash", "parasite"]
    results = []
    
    for film in reference_films:
        # Load key
        key_path = os.path.join(keys_dir, f"{film}.json")
        script_path = os.path.join(scripts_dir, f"{film}.txt")
        
        if not os.path.exists(key_path) or not os.path.exists(script_path):
            logger.error("Missing files for evaluation of %s", film)
            continue
            
        with open(key_path, "r", encoding="utf-8-sig") as f:
            key_data = json.load(f)
            
        with open(script_path, "r", encoding="utf-8-sig") as f:
            script_text = f.read()
            
        page_count = estimate_page_count(script_text)
        
        logger.info("Evaluating structure on %s (%d pages)...", key_data["title"], page_count)
        
        try:
            # Run Structure Agent
            agent_result = await run_structure_agent(script_text, page_count)
            
            # Compare detected page with key
            film_deviations = []
            comparisons = {}
            
            for beat_name, expected_page in key_data["beats"].items():
                # Find matching beat in agent output
                detected_page = None
                for beat_detection in agent_result.beats:
                    if beat_detection.beat_name.lower().strip() == beat_name.lower().strip():
                        detected_page = beat_detection.detected_page
                        break
                
                # Compute absolute deviation in pages and %
                expected_pct = round((expected_page / page_count) * 100, 1)
                
                if detected_page is not None:
                    detected_pct = round((detected_page / page_count) * 100, 1)
                    dev_pct = abs(detected_pct - expected_pct)
                    film_deviations.append(dev_pct)
                    comparisons[beat_name] = {
                        "expected_page": expected_page,
                        "detected_page": detected_page,
                        "expected_pct": expected_pct,
                        "detected_pct": detected_pct,
                        "deviation_pct": dev_pct,
                        "status": "match"
                    }
                else:
                    film_deviations.append(100.0)  # Maximum penalty for missed beat
                    comparisons[beat_name] = {
                        "expected_page": expected_page,
                        "detected_page": None,
                        "expected_pct": expected_pct,
                        "detected_pct": None,
                        "deviation_pct": 100.0,
                        "status": "missed"
                    }
            
            mean_dev = sum(film_deviations) / len(film_deviations) if film_deviations else 100.0
            
            results.append({
                "title": key_data["title"],
                "page_count": page_count,
                "mean_deviation_pct": round(mean_dev, 2),
                "beats": comparisons
            })
            
        except Exception as e:
            logger.exception("Failed to run structure eval for %s", film)
            results.append({
                "title": key_data["title"],
                "error": str(e)
            })
            
    return results

if __name__ == "__main__":
    # Setup simple logging
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(evaluate_structure())
    print(json.dumps(res, indent=2))
