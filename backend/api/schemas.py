"""
Pydantic schemas for the Script Doctor Swarm API.

These models define the wire format for all request / response payloads
and are also used internally as the canonical data structures passed
between agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class Verdict(str, Enum):
    PASS = "PASS"
    CONSIDER = "CONSIDER"
    RECOMMEND = "RECOMMEND"


class Severity(str, Enum):
    MAJOR = "major"
    MINOR = "minor"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Rating(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class ContinuityErrorType(str, Enum):
    PROP = "prop"
    TIMELINE = "timeline"
    FACT = "fact"
    LOCATION = "location"


# ═══════════════════════════════════════════════════════════════════════════
# Structure Agent
# ═══════════════════════════════════════════════════════════════════════════

class BeatDetection(BaseModel):
    beat_name: str = Field(..., description="Name of the beat, e.g. 'Catalyst'")
    expected_pct: float = Field(..., description="Expected percentage position in screenplay")
    detected_page: Optional[int] = Field(None, description="Page where beat was detected")
    detected_pct: Optional[float] = Field(None, description="Actual percentage position")
    deviation_pct: Optional[float] = Field(None, description="|detected - expected|")
    quote: str = Field("", description="Supporting quote from the script")
    confidence: Confidence = Field(Confidence.MEDIUM)


class StructureResult(BaseModel):
    beats: list[BeatDetection] = Field(default_factory=list)
    mean_deviation: Optional[float] = Field(None)
    structural_assessment: str = Field("")


# ═══════════════════════════════════════════════════════════════════════════
# Character Agent
# ═══════════════════════════════════════════════════════════════════════════

class CharacterProfile(BaseModel):
    name: str
    role: str = Field("", description="protagonist / antagonist / supporting")
    stated_motivation: str = Field("")
    arc_summary: str = Field("")
    traits: list[str] = Field(default_factory=list)


class CharacterInconsistency(BaseModel):
    character: str
    page: Optional[int] = None
    description: str = ""
    established_trait: str = ""
    contradicting_action: str = ""
    severity: Severity = Severity.MINOR


class CharacterResult(BaseModel):
    characters: list[CharacterProfile] = Field(default_factory=list)
    inconsistencies: list[CharacterInconsistency] = Field(default_factory=list)
    character_assessment: str = Field("")


# ═══════════════════════════════════════════════════════════════════════════
# Comps / Marketability Agent
# ═══════════════════════════════════════════════════════════════════════════

class CompFilm(BaseModel):
    tmdb_id: int
    title: str
    year: Optional[int] = None
    genres: list[str] = Field(default_factory=list)
    overview: str = ""
    vote_average: Optional[float] = None
    poster_path: Optional[str] = None


class CompsResult(BaseModel):
    extracted_genres: list[str] = Field(default_factory=list)
    extracted_keywords: list[str] = Field(default_factory=list)
    comparable_films: list[CompFilm] = Field(default_factory=list)
    positioning_statement: str = Field("")
    target_audience: str = Field("")
    market_assessment: str = Field("")


# ═══════════════════════════════════════════════════════════════════════════
# Continuity Agent
# ═══════════════════════════════════════════════════════════════════════════

class ContinuityError(BaseModel):
    error_type: ContinuityErrorType = ContinuityErrorType.FACT
    page_introduced: Optional[int] = None
    page_violated: Optional[int] = None
    description: str = ""
    established_fact: str = ""
    contradiction: str = ""
    severity: Severity = Severity.MINOR


class ContinuityResult(BaseModel):
    errors: list[ContinuityError] = Field(default_factory=list)
    continuity_assessment: str = Field("")


# ═══════════════════════════════════════════════════════════════════════════
# Scorecard & Coverage Report  (Synthesizer output)
# ═══════════════════════════════════════════════════════════════════════════

class ScoreCard(BaseModel):
    category: str
    rating: Rating = Rating.FAIR


class CoverageReport(BaseModel):
    """The final, unified coverage report produced by the Synthesizer."""

    # Header
    title: str = ""
    writer: str = ""
    genre: str = ""
    page_count: int = 0

    # Core report
    logline: str = ""
    synopsis: str = ""
    comments: dict[str, str] = Field(
        default_factory=dict,
        description="Category -> commentary (e.g. Structure, Character, ...)",
    )
    scorecard: list[ScoreCard] = Field(default_factory=list)
    verdict: Verdict = Verdict.CONSIDER
    verdict_justification: str = ""

    # Agent detail (for tabbed view)
    structure_detail: Optional[StructureResult | dict] = None
    character_detail: Optional[CharacterResult | dict] = None
    comps_detail: Optional[CompsResult | dict] = None
    continuity_detail: Optional[ContinuityResult | dict] = None


# ═══════════════════════════════════════════════════════════════════════════
# API-level models
# ═══════════════════════════════════════════════════════════════════════════

class CoverageJobResponse(BaseModel):
    job_id: str


class AgentProgressEvent(BaseModel):
    """Payload for a single SSE progress event."""
    event: str = Field(..., description="agent_start | agent_complete | error | complete")
    agent: Optional[str] = Field(None, description="Agent name if applicable")
    message: str = Field("")
    data: Optional[dict] = Field(None, description="Agent result or final report")


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending | running | complete | error
    report: Optional[CoverageReport] = None
    error: Optional[str] = None
