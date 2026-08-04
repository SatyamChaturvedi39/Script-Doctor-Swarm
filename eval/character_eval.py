"""
Character Agent Evaluation.

Evaluates Character Agent consistency flags against a canary script with deliberately planted inconsistencies.
Computes precision and recall.
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

from agents.character_agent import run_character_agent
from parser.extractor import estimate_page_count

from eval_cache import get_cached_result, set_cached_result

logger = logging.getLogger("script_doctor.eval.character")

async def evaluate_character(force: bool = False, delay_seconds: float = 3.0, script_name: str = "canary_02") -> dict:
    cache_key = f"character:{script_name}"
    cached = get_cached_result(cache_key, force=force)
    if cached:
        logger.info("[CACHE HIT] Skipping character evaluation for '%s' (loaded from eval_cache.json)", script_name)
        return cached

    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "data", "canary_scripts")
    
    script_path = os.path.join(scripts_dir, f"{script_name}.txt")
    key_path = os.path.join(scripts_dir, f"{script_name}_key.json")
    
    if not os.path.exists(script_path) or not os.path.exists(key_path):
        logger.error("Missing canary script or key for %s", script_name)
        return {"error": "Missing input files"}
        
    with open(key_path, "r", encoding="utf-8-sig") as f:
        key_data = json.load(f)
        
    with open(script_path, "r", encoding="utf-8-sig") as f:
        script_text = f.read()
        
    page_count = estimate_page_count(script_text)
    
    logger.info("Evaluating Character Agent on %s (%d pages)...", script_name, page_count)
    
    try:
        agent_result = await run_character_agent(script_text, page_count)
        
        # Ground truth character inconsistencies
        ground_truth = key_data.get("character_inconsistencies", [])
        detected = agent_result.inconsistencies
        
        tp = 0
        fp = 0
        fn = 0
        
        matched_gt = set()
        matched_det = set()
        
        # Compare ground truth with detected
        for i_gt, gt in enumerate(ground_truth):
            gt_char = gt["character"].lower().strip()
            # Support both key schema variants: violated_page (current) and established_page (legacy)
            gt_page = gt.get("violated_page") or gt.get("established_page")
            
            for i_det, det in enumerate(detected):
                det_char = det.character.lower().strip()
                det_page = det.page
                
                # Check for match (same character, page +/- 1)
                char_match = gt_char in det_char or det_char in gt_char
                page_match = (
                    det_page is not None 
                    and gt_page is not None 
                    and abs(det_page - gt_page) <= 1
                )
                
                if char_match and page_match:
                    tp += 1
                    matched_gt.add(i_gt)
                    matched_det.add(i_det)
                    break
        
        fp = len(detected) - len(matched_det)
        fn = len(ground_truth) - len(matched_gt)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        res = {
            "total_characters_tracked": len(agent_result.characters),
            "ground_truth_count": len(ground_truth),
            "detected_count": len(detected),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1, 2)
        }
        set_cached_result(cache_key, res)
        
        if delay_seconds > 0:
            logger.info("Pacing delay: sleeping for %.1fs before next call...", delay_seconds)
            await asyncio.sleep(delay_seconds)
            
        return res
        
    except Exception as e:
        logger.exception("Failed to run character eval")
        return {"error": str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(evaluate_character())
    print(json.dumps(res, indent=2))
