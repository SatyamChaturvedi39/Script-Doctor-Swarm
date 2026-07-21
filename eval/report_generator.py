"""
Evaluation Report Generator.

Converts JSON evaluation results into a clean, human-readable Markdown report
with tables summarizing all metrics.
"""

from __future__ import annotations

import os

def generate_markdown_report(summary: dict, timestamp: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    report_md_path = os.path.join(results_dir, f"eval_report_{timestamp}.md")
    
    # 1. Structure Summary Table
    struct_lines = [
        "| Film Title | Pages | Mean Deviation % | Status |",
        "| :--- | :---: | :---: | :--- |"
    ]
    for res in summary.get("structure", []):
        if "error" in res:
            struct_lines.append(f"| {res['title']} | — | — | ERROR: {res['error']} |")
        else:
            struct_lines.append(f"| {res['title']} | {res['page_count']} | {res['mean_deviation_pct']}% | Active |")
            
    # 2. Comps Summary Table
    comps_lines = [
        "| Film Title | Ground Truth Comps | Detected Comps | Overlaps | Overlap % |",
        "| :--- | :--- | :--- | :--- | :---: |"
    ]
    for res in summary.get("comps", []):
        if "error" in res:
            comps_lines.append(f"| {res['title']} | — | — | — | ERROR: {res['error']} |")
        else:
            gt_str = ", ".join(res["ground_truth_comps"])
            det_str = ", ".join(res["detected_comps"])
            ov_str = ", ".join(res["overlaps"]) if res["overlaps"] else "None"
            comps_lines.append(f"| {res['title']} | {gt_str} | {det_str} | {ov_str} | {res['overlap_pct']}% |")
            
    # 3. Character & Continuity (Canary Injection) Summary Table
    char_res = summary.get("character", {})
    cont_res = summary.get("continuity", {})
    
    canary_lines = [
        "| Agent Evaluated | Ground Truth Errors | Detected Errors | True Positives | False Positives | Precision | Recall | F1 Score |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    
    if "error" in char_res:
        canary_lines.append(f"| Character Agent | — | — | — | — | — | — | ERROR: {char_res['error']} |")
    else:
        canary_lines.append(
            f"| Character Agent | {char_res.get('ground_truth_count', 0)} | {char_res.get('detected_count', 0)} | "
            f"{char_res.get('true_positives', 0)} | {char_res.get('false_positives', 0)} | "
            f"{char_res.get('precision', 0.0)} | {char_res.get('recall', 0.0)} | {char_res.get('f1_score', 0.0)} |"
        )
        
    if "error" in cont_res:
        canary_lines.append(f"| Continuity Agent | — | — | — | — | — | — | ERROR: {cont_res['error']} |")
    else:
        canary_lines.append(
            f"| Continuity Agent | {cont_res.get('ground_truth_count', 0)} | {cont_res.get('detected_count', 0)} | "
            f"{cont_res.get('true_positives', 0)} | {cont_res.get('false_positives', 0)} | "
            f"{cont_res.get('precision', 0.0)} | {cont_res.get('recall', 0.0)} | {cont_res.get('f1_score', 0.0)} |"
        )

    # Full report template
    report_content = f"""# Script Doctor Swarm — Evaluation Harness Report

**Run Timestamp:** {summary.get("timestamp")}  
**Duration:** {summary.get("duration_seconds")} seconds  

This report evaluates the accuracy and consistency of the specialized agents within the Script Doctor Swarm.

---

## 1. Structure Agent Evaluation
The Structure Agent is measured against published beat-sheet answer keys for well-known films, computing the mean percentage deviation between detected beat locations and ground truth locations.

{"\n".join(struct_lines)}

---

## 2. Character & Continuity Agents Evaluation (Canary Injection)
Evaluated via a synthetic canary script (`canary_01.txt`) with deliberately planted errors:
- Arthur (strict pacifist) punches a bartender (Character Inconsistency).
- Mark leaves keys on kitchen counter but pulls them from his pocket (Continuity: Prop Error).
- Sarah states she is an only child but mentions her older brother Bobby (Continuity: Fact Error).

{"\n".join(canary_lines)}

---

## 3. Comps/Marketability Agent Evaluation
The Comps Agent is spot-checked against reported trade-press comps for reference films to evaluate overlap percentage.

{"\n".join(comps_lines)}

---

*Note: Evaluation run completed using Gemini Model: `{os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}`.*
"""

    with open(report_md_path, "w") as f:
        f.write(report_content)
        
    return report_md_path
