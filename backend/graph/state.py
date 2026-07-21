"""
LangGraph pipeline state definition.

The state flows through the graph:
  START → [structure, character, comps, continuity] → synthesizer → END

Agent outputs use an `Annotated[list, operator.add]` reducer so that
parallel agents can safely append their results without overwriting
each other.
"""

from __future__ import annotations

import operator
from typing import Annotated, Optional, TypedDict


class AgentOutput(TypedDict):
    """A single agent's contribution to the pipeline state."""
    agent_name: str  # "structure" | "character" | "comps" | "continuity"
    result: dict     # Agent-specific structured output (serialized Pydantic model)


class PipelineState(TypedDict):
    """Shared state passed through the LangGraph pipeline."""

    # ── Input (set once at pipeline start) ──
    script_text: str
    page_count: int
    job_id: str

    # ── Agent outputs (parallel-safe via reducer) ──
    agent_outputs: Annotated[list[AgentOutput], operator.add]

    # ── Final report (set by synthesizer) ──
    report: Optional[dict]
