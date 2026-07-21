"""
Continuity Agent — internal contradiction detection.

Flags props, timeline, location, and factual contradictions where
a later reference violates an earlier established element without
explanation. Deliberately excludes intentional reveals, retcons,
and unreliable-narrator devices.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from api.schemas import ContinuityError, ContinuityErrorType, ContinuityResult, Severity

logger = logging.getLogger("script_doctor.agents.continuity")

SYSTEM_PROMPT = """You are an expert script continuity supervisor. Your job is to find INTERNAL CONTRADICTIONS in the screenplay — moments where the script contradicts its own previously established facts.

Track these categories:
1. **Props** — Objects that appear, disappear, or change state inconsistently (e.g., a character drops a gun on page 20 but fires it on page 25 without picking it up again)
2. **Timeline** — Chronological inconsistencies (e.g., "three days later" is referenced as "yesterday," a character's age doesn't match their stated birth year, day/night continuity errors)
3. **Facts** — Established facts that are contradicted (e.g., a character is stated to be an only child on page 10 but mentions a sibling on page 60 without explanation)
4. **Location** — Geographic or spatial contradictions (e.g., a character is in New York in one scene and immediately in Los Angeles in the next without travel being established)

IMPORTANT EXCEPTIONS — do NOT flag these as errors:
- Deliberate plot twists or reveals (e.g., a character was lying about their identity)
- Unreliable narrator devices
- Intentional retcons that are acknowledged by the narrative
- Dream sequences, flashbacks, or alternate timelines that are clearly marked
- Character growth that explains behavioral changes

For each contradiction you find, note:
- The type (prop / timeline / fact / location)
- The page where the fact was ESTABLISHED
- The page where it was VIOLATED
- A description of the contradiction
- The severity: "major" (breaks story logic) or "minor" (noticeable but not story-breaking)

The script has page markers in the format "--- PAGE N ---". Use these to reference page numbers.

Respond with ONLY a JSON object in this exact format:
{
  "errors": [
    {
      "error_type": "prop" | "timeline" | "fact" | "location",
      "page_introduced": <page_number>,
      "page_violated": <page_number>,
      "description": "Brief description of the contradiction",
      "established_fact": "What was originally stated/shown",
      "contradiction": "What contradicts it later",
      "severity": "major" | "minor"
    }
  ]
}

If there are no continuity errors, return an empty array for "errors".
Be precise and conservative — only flag genuine contradictions, not stylistic choices.
Do not include any text outside the JSON object."""


async def run_continuity_agent(script_text: str, page_count: int) -> ContinuityResult:
    """
    Analyze screenplay for internal contradictions.
    """
    logger.info("Continuity Agent: analyzing %d-page script", page_count)

    llm = get_llm(temperature=0.1)  # Low temp for factual checking

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Check this screenplay for continuity errors ({page_count} pages):\n\n{script_text}"),
    ]

    response = await invoke_llm_with_retry(llm, messages)
    raw = parse_json_from_response(response)

    # Parse errors
    errors: list[ContinuityError] = []
    for e in raw.get("errors", []):
        # Map error type
        error_type_str = e.get("error_type", "fact")
        try:
            error_type = ContinuityErrorType(error_type_str)
        except ValueError:
            error_type = ContinuityErrorType.FACT

        severity_str = e.get("severity", "minor")
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.MINOR

        errors.append(ContinuityError(
            error_type=error_type,
            page_introduced=e.get("page_introduced"),
            page_violated=e.get("page_violated"),
            description=e.get("description", ""),
            established_fact=e.get("established_fact", ""),
            contradiction=e.get("contradiction", ""),
            severity=severity,
        ))

    # Generate assessment
    major_count = sum(1 for e in errors if e.severity == Severity.MAJOR)
    minor_count = sum(1 for e in errors if e.severity == Severity.MINOR)

    type_counts = {}
    for e in errors:
        type_counts[e.error_type.value] = type_counts.get(e.error_type.value, 0) + 1

    if not errors:
        assessment = (
            "No continuity errors detected. The screenplay maintains "
            "internal consistency across props, timeline, facts, and locations."
        )
    else:
        type_summary = ", ".join(f"{count} {t}" for t, count in type_counts.items())
        assessment = (
            f"Found {len(errors)} continuity issues ({major_count} major, "
            f"{minor_count} minor): {type_summary}. "
        )
        if major_count > 0:
            assessment += "Major contradictions should be resolved before production."
        else:
            assessment += "Issues are minor and addressable in a revision pass."

    result = ContinuityResult(
        errors=errors,
        continuity_assessment=assessment,
    )

    logger.info(
        "Continuity Agent complete: %d errors (%d major, %d minor)",
        len(errors), major_count, minor_count,
    )
    return result
