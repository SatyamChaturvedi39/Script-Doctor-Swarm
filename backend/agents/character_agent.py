"""
Character Agent — arc tracking and inconsistency detection.

Two-pass analysis:
  1. Extract all named characters, their motivations, roles, and traits.
  2. Scan for moments that contradict established traits without
     narrative justification.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from api.schemas import (
    CharacterInconsistency,
    CharacterProfile,
    CharacterResult,
    Severity,
)

logger = logging.getLogger("script_doctor.agents.character")

SYSTEM_PROMPT = """You are an expert screenplay character analyst. Your task is to:

1. IDENTIFY all significant named characters in the screenplay (up to 10 most important). 
   - Note: The screenplay text may use non-standard formatting (e.g. ALL-CAPS dialogue headers "JOHNNY", transcript style "Johnny:", or inline stage directions). Look for recurring character names speaking or taking action throughout the text regardless of format.

2. For each character, determine:
   - Their role (protagonist / antagonist / supporting)
   - Their stated motivation (what they explicitly want)
   - A brief summary of their character arc (how they change or fail to change)
   - 3-5 defining traits established in the script

3. FLAG any moments where a character acts INCONSISTENTLY with their established traits WITHOUT narrative justification. This means:
   - A previously established trait is violated (e.g., a confirmed pacifist suddenly uses violence without provocation, explanation, or character growth leading to that moment)
   - Do NOT flag: deliberate character growth, earned revelations, intentional twists, or moments where the script provides context for the change
   - For each inconsistency, note: the character, the page number, what trait was established, what contradicting action occurred, and whether the inconsistency is major (breaks believability) or minor (a small departure)

The script has page markers in the format "--- PAGE N ---". Use these to reference page numbers.

Respond with ONLY a JSON object in this exact format:
{
  "characters": [
    {
      "name": "CHARACTER NAME",
      "role": "protagonist" | "antagonist" | "supporting",
      "stated_motivation": "What they want",
      "arc_summary": "How they change over the story",
      "traits": ["trait1", "trait2", "trait3"]
    }
  ],
  "inconsistencies": [
    {
      "character": "CHARACTER NAME",
      "page": <page_number>,
      "description": "Brief description of the inconsistency",
      "established_trait": "The trait that was established earlier",
      "contradicting_action": "The action that contradicts it",
      "severity": "major" | "minor"
    }
  ]
}

If there are no inconsistencies, return an empty array for "inconsistencies".
Do not include any text outside the JSON object."""


async def run_character_agent(script_text: str, page_count: int) -> CharacterResult:
    """
    Analyze characters: extract profiles and flag inconsistencies.
    """
    logger.info("Character Agent: analyzing %d-page script (length: %d chars)", page_count, len(script_text))

    llm = get_llm(temperature=0.2)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze the characters in this screenplay ({page_count} pages):\n\n{script_text}"),
    ]

    response = await invoke_llm_with_retry(llm, messages)
    raw = parse_json_from_response(response)

    # Parse characters
    characters: list[CharacterProfile] = []
    for c in raw.get("characters", []):
        char_name = c.get("name", "Unknown").strip()
        if char_name:
            logger.info("Character Agent: identified character: %s (role: %s)", char_name, c.get("role"))
            characters.append(CharacterProfile(
                name=char_name,
                role=c.get("role", "supporting"),
                stated_motivation=c.get("stated_motivation", ""),
                arc_summary=c.get("arc_summary", ""),
                traits=c.get("traits", []),
            ))

    logger.info("Character Agent: extracted %d character profiles: %s", len(characters), [c.name for c in characters])

    # Parse inconsistencies
    inconsistencies: list[CharacterInconsistency] = []
    for inc in raw.get("inconsistencies", []):
        severity_str = inc.get("severity", "minor")
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.MINOR

        inconsistencies.append(CharacterInconsistency(
            character=inc.get("character", "Unknown"),
            page=inc.get("page"),
            description=inc.get("description", ""),
            established_trait=inc.get("established_trait", ""),
            contradicting_action=inc.get("contradicting_action", ""),
            severity=severity,
        ))

    # Generate assessment & Guard for empty/insufficient character extraction
    major_count = sum(1 for i in inconsistencies if i.severity == Severity.MAJOR)
    minor_count = sum(1 for i in inconsistencies if i.severity == Severity.MINOR)

    if len(characters) == 0:
        logger.warning("Character Agent: 0 characters extracted from script formatting.")
        assessment = (
            "Insufficient character data extracted from script text formatting. "
            "No character profiles could be tracked for inconsistency analysis."
        )
    elif not inconsistencies:
        assessment = (
            f"Character work is consistent across {len(characters)} tracked characters "
            f"({', '.join(c.name for c in characters[:4])}). "
            f"No significant trait violations detected."
        )
    else:
        assessment = (
            f"Tracked {len(characters)} characters. Found {len(inconsistencies)} "
            f"inconsistencies ({major_count} major, {minor_count} minor). "
        )
        if major_count > 0:
            assessment += "Major inconsistencies should be addressed to maintain character believability."
        else:
            assessment += "Minor inconsistencies noted but character arcs are broadly coherent."

    result = CharacterResult(
        characters=characters,
        inconsistencies=inconsistencies,
        character_assessment=assessment,
    )

    logger.info(
        "Character Agent complete: %d characters, %d inconsistencies",
        len(characters), len(inconsistencies),
    )
    return result
