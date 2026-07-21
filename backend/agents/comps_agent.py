"""
Comps / Marketability Agent — TMDB-grounded comparable films.

CRITICAL CONSTRAINT: All comparable film suggestions MUST come from
TMDB API results. The LLM must NEVER suggest comp titles from its own
memory. This is enforced by a three-phase pipeline:

  Phase 1 (LLM):  Extract genre, keywords, tone, budget tier from script
  Phase 2 (TMDB): Retrieve real matching films via the TMDB API
  Phase 3 (LLM):  Write positioning language grounded ONLY in retrieved films
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import get_llm, invoke_llm_with_retry, parse_json_from_response
from api.schemas import CompFilm, CompsResult
from services.tmdb_client import find_comparable_films

logger = logging.getLogger("script_doctor.agents.comps")

# ── Phase 1: Extract genres and keywords ──────────────────────────────────
EXTRACTION_PROMPT = """You are a film industry analyst. Analyze this screenplay and extract:

1. **Genres** — The 2-3 most fitting film genres (use standard TMDB genre names: Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, TV Movie, Thriller, War, Western)

2. **Keywords** — 5-8 thematic/plot keywords that would help find similar films (e.g., "time travel", "heist", "coming of age", "revenge", "alien invasion", "courtroom drama")

3. **Tone** — The overall tone (e.g., "dark and gritty", "lighthearted comedy", "psychological thriller")

4. **Budget tier** — Estimated production budget tier: "micro" (<$5M), "low" ($5-20M), "mid" ($20-80M), "high" ($80M+)

Respond with ONLY a JSON object:
{
  "genres": ["Genre1", "Genre2"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "tone": "description of tone",
  "budget_tier": "micro" | "low" | "mid" | "high"
}

Do NOT suggest any comparable film titles. Only extract descriptors.
Do not include any text outside the JSON object."""


# ── Phase 3: Generate positioning language ────────────────────────────────
POSITIONING_PROMPT = """You are a film industry marketing analyst. Based on the screenplay analysis and the REAL comparable films retrieved from TMDB, write:

1. A positioning statement (2-3 sentences) describing where this script sits in the current market landscape.
2. A target audience description (2-3 sentences) identifying who would be most likely to watch this film.
3. A market assessment (2-3 sentences) evaluating the commercial potential.

SCREENPLAY ANALYSIS:
Genres: {genres}
Keywords: {keywords}
Tone: {tone}
Budget tier: {budget_tier}

COMPARABLE FILMS FROM TMDB (these are REAL films — use ONLY these as comparisons):
{films_text}

CRITICAL RULES:
- Reference ONLY the films listed above as comparisons. Do NOT add films from your own knowledge.
- Frame comparisons naturally (e.g., "In the vein of [Film1] and [Film2]...")
- Be specific about what aspects are comparable (genre, tone, audience, box office performance)

Respond with ONLY a JSON object:
{{
  "positioning_statement": "...",
  "target_audience": "...",
  "market_assessment": "..."
}}

Do not include any text outside the JSON object."""


async def run_comps_agent(script_text: str, page_count: int) -> CompsResult:
    """
    Three-phase comps analysis: extract → retrieve → position.
    All comps grounded in TMDB results, never LLM memory.
    """
    logger.info("Comps Agent: starting 3-phase analysis")

    llm = get_llm(temperature=0.3)

    # ── Phase 1: Extract genres and keywords from script ──
    logger.info("Comps Agent Phase 1: extracting genres/keywords")
    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=f"Analyze this screenplay ({page_count} pages):\n\n{script_text}"),
    ]
    response = await invoke_llm_with_retry(llm, messages)
    extraction = parse_json_from_response(response)

    genres = extraction.get("genres", ["Drama"])
    keywords = extraction.get("keywords", [])
    tone = extraction.get("tone", "")
    budget_tier = extraction.get("budget_tier", "mid")

    logger.info("Comps Agent Phase 1 complete: genres=%s keywords=%s", genres, keywords[:5])

    # ── Phase 2: Retrieve real films from TMDB ──
    logger.info("Comps Agent Phase 2: querying TMDB")
    try:
        tmdb_films = await find_comparable_films(
            genres=genres,
            keywords=keywords,
            min_year=2010,
            max_results=5,
        )
    except Exception as e:
        logger.error("TMDB retrieval failed: %s", e)
        tmdb_films = []

    # Convert to CompFilm schema
    comparable_films: list[CompFilm] = []
    for f in tmdb_films:
        comparable_films.append(CompFilm(
            tmdb_id=f["tmdb_id"],
            title=f["title"],
            year=f.get("year"),
            genres=f.get("genres", []),
            overview=f.get("overview", ""),
            vote_average=f.get("vote_average"),
            poster_path=f.get("poster_path"),
        ))

    logger.info("Comps Agent Phase 2 complete: %d films retrieved", len(comparable_films))

    # ── Phase 3: Generate positioning language ──
    if comparable_films:
        logger.info("Comps Agent Phase 3: generating positioning language")
        films_text = "\n".join(
            f"- {f.title} ({f.year}) — Genres: {', '.join(f.genres)}. "
            f"Rating: {f.vote_average}/10. {f.overview[:150]}"
            for f in comparable_films
        )

        positioning_prompt = POSITIONING_PROMPT.format(
            genres=", ".join(genres),
            keywords=", ".join(keywords),
            tone=tone,
            budget_tier=budget_tier,
            films_text=films_text,
        )

        messages = [
            SystemMessage(content=positioning_prompt),
            HumanMessage(content="Generate the positioning analysis."),
        ]
        response = await invoke_llm_with_retry(llm, messages)
        positioning = parse_json_from_response(response)

        positioning_statement = positioning.get("positioning_statement", "")
        target_audience = positioning.get("target_audience", "")
        market_assessment = positioning.get("market_assessment", "")
    else:
        positioning_statement = "Unable to retrieve comparable films from TMDB."
        target_audience = "Could not determine target audience without comparable films."
        market_assessment = "Market assessment unavailable."

    result = CompsResult(
        extracted_genres=genres,
        extracted_keywords=keywords,
        comparable_films=comparable_films,
        positioning_statement=positioning_statement,
        target_audience=target_audience,
        market_assessment=market_assessment,
    )

    logger.info("Comps Agent complete: %d comps, positioning generated", len(comparable_films))
    return result
