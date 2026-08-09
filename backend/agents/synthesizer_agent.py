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
- COMPS GROUNDING RULE (MANDATORY — THIS APPLIES TO THE ENTIRE REPORT, NOT ONLY THE MARKETABILITY SECTION):
  - If comparable_films_available = TRUE: you MAY reference the provided retrieved film titles by name in your marketability commentary and verdict justification. Reference ONLY the explicitly listed films.
  - If comparable_films_available = FALSE: you MUST NOT mention ANY specific film title ANYWHERE in your response — not in the marketability section, not in the verdict justification, not in the logline, not in the synopsis, and not in any other field. This prohibition is absolute. Do NOT use phrases like "in the vein of", "similar to", "comparable to", or any other construction that names or alludes to a specific film title. Assess marketability only using genre, tone, budget tier, and audience signals. Generating any film title from your own memory when no TMDB films were retrieved is a hallucination that violates this system's core constraint.
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

    # Check whether Comps Agent actually retrieved real TMDB films
    comps_films = comps_data.get("comparable_films", []) if isinstance(comps_data, dict) else []
    comps_available = len(comps_films) > 0
    comps_availability_note = (
        f"comparable_films_available = TRUE ({len(comps_films)} films retrieved from TMDB)"
        if comps_available
        else "comparable_films_available = FALSE — NO films were retrieved from TMDB. Do NOT invent or mention any specific film titles in the marketability section."
    )

    # Build input representation for the LLM
    input_text = f"""
PAGE COUNT: {page_count}

COMPS GROUNDING STATUS: {comps_availability_note}

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

    # Post-generation safety net: if comps were NOT available, scrub any field
    # in the report that contains a quoted film title pattern (e.g. italicised or
    # capitalised title references). We replace the marketability and verdict
    # justification fields with safe fallbacks to prevent hallucinated comp leakage.
    if not comps_available:
        _FILM_CITE_MARKERS = ["in the vein of", "similar to", "comparable to", "like ", "akin to", "reminiscent of"]
        for field_path, fallback in [
            (("comments", "marketability"),
             "No grounded comparable films were retrieved from the TMDB database for this script. "
             "Marketability has been assessed on the basis of genre, tone, and audience profile alone, "
             "without reference to specific produced titles."),
            (("verdict_justification",),
             raw.get("verdict_justification", "")),  # will be checked below
        ]:
            # Navigate to the field
            node = raw
            for key in field_path[:-1]:
                node = node.get(key, {})
            leaf_key = field_path[-1]
            field_value = node.get(leaf_key, "") if isinstance(node, dict) else ""
            if any(marker in field_value.lower() for marker in _FILM_CITE_MARKERS):
                if isinstance(node, dict):
                    if field_path == ("verdict_justification",):
                        # Strip only the offending sentence fragments rather than wiping the field
                        cleaned = " ".join(
                            sentence for sentence in field_value.split(". ")
                            if not any(m in sentence.lower() for m in _FILM_CITE_MARKERS)
                        )
                        node[leaf_key] = cleaned or field_value
                    else:
                        node[leaf_key] = fallback


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
