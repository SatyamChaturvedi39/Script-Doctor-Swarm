"""
Structure Agent — Save the Cat beat detection.

Detects the 7 major screenplay beats and measures deviation from
expected page-percentage positions. The deviation is computed
programmatically; the LLM only identifies beat locations.

Expected beats (from the 15-beat Save the Cat sheet, selecting the
7 major structural turning points):

  1. Catalyst         — ~11%
  2. Break Into Two   — ~23%
  3. B Story          — ~27%
  4. Midpoint         — ~50%
  5. All Is Lost      — ~68%
  6. Break Into Three — ~77%
  7. Final Image      — ~100%
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from api.schemas import BeatDetection, Confidence, StructureResult

logger = logging.getLogger("script_doctor.agents.structure")

# ── Expected beat positions ──────────────────────────────────────────────
EXPECTED_BEATS = [
    {"beat_name": "Catalyst",         "expected_pct": 11.0},
    {"beat_name": "Break Into Two",   "expected_pct": 23.0},
    {"beat_name": "B Story",          "expected_pct": 27.0},
    {"beat_name": "Midpoint",         "expected_pct": 50.0},
    {"beat_name": "All Is Lost",      "expected_pct": 68.0},
    {"beat_name": "Break Into Three", "expected_pct": 77.0},
    {"beat_name": "Final Image",      "expected_pct": 100.0},
]

SYSTEM_PROMPT = """You are an expert screenplay structure analyst. Your task is to identify the 7 major Save the Cat beats in the provided screenplay.

For EACH of the following beats, identify the PAGE NUMBER where it occurs and provide a brief supporting quote (1-2 sentences from the script):

1. **Catalyst** (~11% of script) — The inciting incident that disrupts the hero's ordinary world and forces a decision. Something happens TO the protagonist.

2. **Break Into Two** (~23%) — The protagonist makes an active choice to enter the new world / embark on the journey. This is the Act I → Act II transition.

3. **B Story** (~27%) — The introduction of a secondary relationship (often a love interest or mentor) that carries the thematic argument.

4. **Midpoint** (~50%) — A major shift: either a false victory or false defeat. Stakes are raised. The protagonist moves from reactive to proactive (or vice versa).

5. **All Is Lost** (~68%) — The lowest point. The protagonist's plan has failed, an ally may be lost, and the situation appears hopeless. Often a "whiff of death."

6. **Break Into Three** (~77%) — The protagonist has a synthesis moment, combining A and B stories, and chooses to face the final challenge. Act II → Act III transition.

7. **Final Image** (~100%) — The last scene or image that mirrors/contrasts the Opening Image, showing how the world or protagonist has changed.

The script has page markers in the format "--- PAGE N ---". Use these to identify page numbers.

Respond with ONLY a JSON object in this exact format:
{
  "beats": [
    {
      "beat_name": "Catalyst",
      "detected_page": <page_number_or_null>,
      "quote": "<brief supporting quote from the script>",
      "confidence": "high" | "medium" | "low"
    },
    ... (one entry for each of the 7 beats)
  ]
}

If you cannot identify a beat, set detected_page to null and confidence to "low".
Do not include any text outside the JSON object."""


async def run_structure_agent(script_text: str, page_count: int) -> StructureResult:
    """
    Analyze screenplay structure by detecting the 7 major beats.

    Returns StructureResult with per-beat deviations and a mean deviation score.
    """
    logger.info("Structure Agent: analyzing %d-page script", page_count)

    llm = get_llm(temperature=0.1)  # Low temp for factual detection

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this screenplay ({page_count} pages):\n\n{script_text}"),
    ]

    response = await invoke_llm_with_retry(llm, messages)
    raw = parse_json_from_response(response)

    # Build beat detections with programmatic deviation calculation
    beats: list[BeatDetection] = []
    raw_beats = raw.get("beats", [])

    for expected in EXPECTED_BEATS:
        beat_name = expected["beat_name"]
        expected_pct = expected["expected_pct"]

        # Find matching beat in LLM response
        found = None
        for rb in raw_beats:
            if rb.get("beat_name", "").lower().strip() == beat_name.lower().strip():
                found = rb
                break

        detected_page = found.get("detected_page") if found else None
        quote = found.get("quote", "") if found else ""
        confidence_str = found.get("confidence", "low") if found else "low"

        # Map confidence string to enum
        try:
            confidence = Confidence(confidence_str)
        except ValueError:
            confidence = Confidence.LOW

        # Compute deviation programmatically
        detected_pct = None
        deviation_pct = None
        if detected_page is not None and page_count > 0:
            detected_pct = round((detected_page / page_count) * 100, 1)
            deviation_pct = round(abs(detected_pct - expected_pct), 1)

        beats.append(BeatDetection(
            beat_name=beat_name,
            expected_pct=expected_pct,
            detected_page=detected_page,
            detected_pct=detected_pct,
            deviation_pct=deviation_pct,
            quote=quote,
            confidence=confidence,
        ))

    # Calculate mean deviation (only for beats that were detected)
    deviations = [b.deviation_pct for b in beats if b.deviation_pct is not None]
    mean_deviation = round(sum(deviations) / len(deviations), 1) if deviations else None

    # Generate structural assessment
    if mean_deviation is not None:
        if mean_deviation < 5:
            assessment_quality = "tightly structured"
        elif mean_deviation < 10:
            assessment_quality = "well-structured with minor pacing variations"
        elif mean_deviation < 20:
            assessment_quality = "loosely structured with notable pacing issues"
        else:
            assessment_quality = "significantly departs from conventional structure"

        detected_count = len(deviations)
        structural_assessment = (
            f"The screenplay is {assessment_quality}. "
            f"{detected_count} of 7 major beats were identified with a "
            f"mean deviation of {mean_deviation}% from expected positions."
        )
    else:
        structural_assessment = (
            "Unable to reliably detect structural beats. "
            "The screenplay may use an unconventional narrative structure."
        )

    result = StructureResult(
        beats=beats,
        mean_deviation=mean_deviation,
        structural_assessment=structural_assessment,
    )

    logger.info(
        "Structure Agent complete: %d beats detected, mean deviation=%.1f%%",
        len(deviations), mean_deviation or 0,
    )
    return result
