"""
Synthesizer Agent — Merges all four agent outputs into a standard industry coverage report.

Outputs: Logline, synopsis, per-category comments, scorecard grid, and final verdict with justification.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from api.schemas import CoverageReport, Rating, ScoreCard, Verdict

logger = logging.getLogger("script_doctor.agents.synthesizer")

SYSTEM_PROMPT = """You are an expert studio story analyst and synthesizer.
Your task is to merge the findings of four specialized script analysis agents (Structure, Character, Comps, and Continuity) into a professional, cohesive, and industry-standard script coverage report.

You must generate:
1. **Title, Writer, Genre** (deduced from the script or general context, or set to placeholder if completely absent)
2. **Logline** — A 1-2 sentence core premise identifying the protagonist, their goal, and the stakes.
3. **Synopsis** — A detailed but concise narrative summary of the script (around 500-1000 words).
4. **Comments** — Professional feedback categorized into:
   - **Structure**: Commentary on pacing, beat-sheet deviations, and plot progression.
   - **Character**: Evaluation of character consistency, motivation, and arcs.
   - **Dialogue**: Evaluation of the voice, subtext, and distinction of dialogue.
   - **Marketability**: Marketing position, target audience, and comparison analysis.
   - **Continuity**: Discussion of any plot holes or continuity errors.
5. **Scorecard** — A rating (Excellent, Good, Fair, Poor) for the following categories:
   - "Structure"
   - "Character"
   - "Dialogue"
   - "Marketability"
   - "Continuity"
6. **Verdict** — Decide on a final verdict: "PASS" (not suitable), "CONSIDER" (has potential, needs work), or "RECOMMEND" (exceptional, must-buy).
7. **Verdict Justification** — A robust paragraph justifying the verdict based on the findings.

CRITICAL INSTRUCTIONS:
- You must synthesize findings. For example, if the Continuity Agent found major contradictions, reflect this in the Continuity comments, scorecard rating, and verdict.
- If the Comps Agent suggested comparable films, reference them in the Marketability comments and the positioning statement.
- Maintain an objective, professional studio reader tone.

Respond with ONLY a JSON object in this exact format:
{
  "title": "Title of screenplay",
  "writer": "Writer's name",
  "genre": "Genre",
  "logline": "...",
  "synopsis": "...",
  "comments": {
    "structure": "...",
    "character": "...",
    "dialogue": "...",
    "marketability": "...",
    "continuity": "..."
  },
  "scorecard": [
    {"category": "Structure", "rating": "Excellent" | "Good" | "Fair" | "Poor"},
    {"category": "Character", "rating": "Excellent" | "Good" | "Fair" | "Poor"},
    {"category": "Dialogue", "rating": "Excellent" | "Good" | "Fair" | "Poor"},
    {"category": "Marketability", "rating": "Excellent" | "Good" | "Fair" | "Poor"},
    {"category": "Continuity", "rating": "Excellent" | "Good" | "Fair" | "Poor"}
  ],
  "verdict": "PASS" | "CONSIDER" | "RECOMMEND",
  "verdict_justification": "..."
}

Do not include any text outside the JSON object."""

async def run_synthesizer_agent(
    page_count: int,
    structure_data: dict,
    character_data: dict,
    comps_data: dict,
    continuity_data: dict
) -> CoverageReport:
    """
    Synthesize all agent outputs into a standard coverage report.
    """
    logger.info("Synthesizer Agent: starting synthesis")
    llm = get_llm(temperature=0.3)

    # Build input representation for the LLM
    input_text = f"""
PAGE COUNT: {page_count}

STRUCTURE FINDINGS:
{structure_data}

CHARACTER FINDINGS:
{character_data}

COMPS & MARKETABILITY FINDINGS:
{comps_data}

CONTINUITY FINDINGS:
{continuity_data}
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=input_text),
    ]

    response = await invoke_llm_with_retry(llm, messages)
    raw = parse_json_from_response(response)

    # Convert to CoverageReport schema
    comments = raw.get("comments", {})
    scorecard_raw = raw.get("scorecard", [])
    scorecard: list[ScoreCard] = []
    for item in scorecard_raw:
        cat = item.get("category", "")
        rating_str = item.get("rating", "Fair")
        try:
            rating = Rating(rating_str)
        except ValueError:
            rating = Rating.FAIR
        scorecard.append(ScoreCard(category=cat, rating=rating))

    verdict_str = raw.get("verdict", "CONSIDER").upper()
    try:
        verdict = Verdict(verdict_str)
    except ValueError:
        verdict = Verdict.CONSIDER

    # Create the structured coverage report
    report = CoverageReport(
        title=raw.get("title", "Unknown Title"),
        writer=raw.get("writer", "Unknown Writer"),
        genre=raw.get("genre", "Unknown Genre"),
        page_count=page_count,
        logline=raw.get("logline", ""),
        synopsis=raw.get("synopsis", ""),
        comments={
            "Structure": comments.get("structure", ""),
            "Character": comments.get("character", ""),
            "Dialogue": comments.get("dialogue", ""),
            "Marketability": comments.get("marketability", ""),
            "Continuity": comments.get("continuity", "")
        },
        scorecard=scorecard,
        verdict=verdict,
        verdict_justification=raw.get("verdict_justification", ""),
        structure_detail=structure_data,
        character_detail=character_data,
        comps_detail=comps_data,
        continuity_detail=continuity_data
    )

    logger.info("Synthesizer Agent complete. Verdict: %s", verdict.value)
    return report
