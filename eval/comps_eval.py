"""
Comps Agent Evaluation.

Spot-checks the Comps Agent suggested movies against documented trade-press comparable films.
Computes overlap percentage.
"""

from __future__ import annotations

import os
import sys
import json
import logging
import asyncio

# Ensure backend directory is in sys.path when running standalone or imported
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from agents.comps_agent import run_comps_agent
from parser.extractor import estimate_page_count

from eval_cache import get_cached_result, set_cached_result

logger = logging.getLogger("script_doctor.eval.comps")

async def evaluate_comps(force: bool = False, delay_seconds: float = 3.0, films: list[str] | None = None) -> list[dict]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ref_dir = os.path.join(base_dir, "data", "comps_reference")
    scripts_dir = os.path.join(base_dir, "data", "canary_scripts")
    
    ref_path = os.path.join(ref_dir, "comps_reference.json")
    
    if not os.path.exists(ref_path):
        logger.error("Missing trade-press comps reference file.")
        return []
        
    with open(ref_path, "r", encoding="utf-8-sig") as f:
        comps_reference = json.load(f)
        
    reference_films = films or ["get_out", "whiplash", "parasite"]
    results = []
    
    for film_key in reference_films:
        cache_key = f"comps:{film_key}"
        cached = get_cached_result(cache_key, force=force)
        if cached:
            logger.info("[CACHE HIT] Skipping comps evaluation for '%s' (loaded from eval_cache.json)", film_key)
            results.append(cached)
            continue

        script_path = os.path.join(scripts_dir, f"{film_key}.txt")
        if not os.path.exists(script_path):
            logger.error("Missing script for %s", film_key)
            continue
            
        with open(script_path, "r", encoding="utf-8-sig") as f:
            script_text = f.read()
            
        page_count = estimate_page_count(script_text)
        
        # Determine human-readable title matching the keys in comps_reference
        film_title = "Get Out" if film_key == "get_out" else ("Whiplash" if film_key == "whiplash" else "Parasite")
        ground_truth_comps = comps_reference.get(film_title, [])
        
        logger.info("Evaluating Comps Agent on %s (%d pages)...", film_title, page_count)
        
        try:
            agent_result = await run_comps_agent(script_text, page_count)
            detected_comps = [f.title for f in agent_result.comparable_films]
            
            # Count overlaps (case-insensitive name comparison)
            overlaps = []
            for dt in detected_comps:
                dt_clean = dt.lower().strip()
                for gt in ground_truth_comps:
                    gt_clean = gt.lower().strip()
                    if gt_clean in dt_clean or dt_clean in gt_clean:
                        overlaps.append(dt)
                        break
            
            overlap_pct = (len(overlaps) / len(ground_truth_comps)) * 100 if ground_truth_comps else 0.0
            
            res_dict = {
                "title": film_title,
                "ground_truth_comps": ground_truth_comps,
                "detected_comps": detected_comps,
                "overlaps": overlaps,
                "overlap_count": len(overlaps),
                "overlap_pct": round(overlap_pct, 1)
            }
            set_cached_result(cache_key, res_dict)
            results.append(res_dict)
            
            if delay_seconds > 0:
                logger.info("Pacing delay: sleeping for %.1fs before next call...", delay_seconds)
                await asyncio.sleep(delay_seconds)
            
        except Exception as e:
            logger.exception("Failed to run comps eval for %s", film_title)
            results.append({
                "title": film_title,
                "error": str(e)
            })
            
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(evaluate_comps())
    print(json.dumps(res, indent=2))
