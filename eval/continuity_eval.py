"""
Continuity Agent Evaluation.

Evaluates Continuity Agent error flags against a canary script with deliberately planted continuity errors.
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

from agents.continuity_agent import run_continuity_agent
from parser.extractor import estimate_page_count

from eval_cache import get_cached_result, set_cached_result

logger = logging.getLogger("script_doctor.eval.continuity")

async def evaluate_continuity(force: bool = False, delay_seconds: float = 3.0, script_name: str = "canary_02") -> dict:
    cache_key = f"continuity:{script_name}"
    cached = get_cached_result(cache_key, force=force)
    if cached:
        logger.info("[CACHE HIT] Skipping continuity evaluation for '%s' (loaded from eval_cache.json)", script_name)
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
    
    logger.info("Evaluating Continuity Agent on %s (%d pages)...", script_name, page_count)
    
    try:
        agent_result = await run_continuity_agent(script_text, page_count)
        
        # Ground truth continuity errors
        ground_truth = key_data.get("continuity_errors", [])
        detected = agent_result.errors
        
        tp = 0
        fp = 0
        fn = 0
        
        matched_gt = set()
        matched_det = set()
        
        # Compare ground truth with detected
        for i_gt, gt in enumerate(ground_truth):
            gt_type = gt["error_type"].lower().strip()
            # Support both key schema variants: page_violated (current) and violated_page (legacy)
            gt_page_violated = gt.get("page_violated") or gt.get("violated_page")
            
            for i_det, det in enumerate(detected):
                det_type = det.error_type.value.lower().strip()
                det_page_violated = det.page_violated
                
                # Check for match (same error category type, violated page +/- 1)
                type_match = gt_type == det_type or (gt_type == "prop" and det_type == "fact")  # Lenient type match
                page_match = (
                    det_page_violated is not None 
                    and gt_page_violated is not None 
                    and abs(det_page_violated - gt_page_violated) <= 1
                )
                
                if type_match and page_match:
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
        logger.exception("Failed to run continuity eval")
        return {"error": str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(evaluate_continuity())
    print(json.dumps(res, indent=2))
