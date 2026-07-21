# Script Doctor Swarm — Evaluation Harness

This directory contains the automated evaluation suite for measuring the accuracy and performance of the Script Doctor Swarm agents.

## Evaluation Structure

1. **Structure Agent:** Tested against published beat-sheet answer keys for well-known films (*The Dark Knight*, *Get Out*, *Jaws*). Measures the mean absolute percentage deviation between detected page-positions and documented ones.
2. **Character & Continuity Agents:** Tested via a synthetic canary script (`canary_01.txt`) containing 3 deliberately planted errors (1 character inconsistency and 2 continuity errors). Computes precision and recall on catching them.
3. **Comps Agent:** Spot-checked against reported trade-press comps for reference films to evaluate overlap percentage.

## How to Run

1. Make sure you have your API keys in the `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   TMDB_API_KEY=your_tmdb_api_key
   ```
2. Navigate to the `eval` directory and run the runner:
   ```bash
   python run_eval.py
   ```
3. The evaluation outputs will be saved in `eval/results/` as both JSON raw data and a human-readable Markdown report:
   - `eval_report_<timestamp>.json`
   - `eval_report_<timestamp>.md`
