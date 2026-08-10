"""
LangGraph graph definition.

Defines the flow:
START -> [structure_node, character_node, comps_node, continuity_node] -> synthesizer_node -> END
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from graph.state import PipelineState, AgentOutput
from agents.structure_agent import run_structure_agent
from agents.character_agent import run_character_agent
from agents.comps_agent import run_comps_agent
from agents.continuity_agent import run_continuity_agent
from agents.synthesizer_agent import run_synthesizer_agent
from api.jobs import push_event

logger = logging.getLogger("script_doctor.graph.pipeline")

import asyncio

# ── Node Functions ─────────────────────────────────────────────────────────

async def structure_node(state: PipelineState) -> Dict[str, Any]:
    """Execute Structure Agent."""
    job_id = state["job_id"]
    logger.info("Executing Structure Agent node for job: %s", job_id)
    await push_event(job_id, {"event": "agent_start", "agent": "structure", "message": "Structure Agent analyzing screenplay beats..."})
    
    try:
        # Cap at 80,000 chars (~40 pages) to prevent OOM on free-tier hosting
        text = state["script_text"][:80000] if len(state["script_text"]) > 80000 else state["script_text"]
        res = await run_structure_agent(text, state["page_count"])
        result_dict = res.model_dump()
        await push_event(job_id, {
            "event": "agent_complete", 
            "agent": "structure", 
            "message": "Structure Agent analysis complete.",
            "data": result_dict
        })
        return {"agent_outputs": [{"agent_name": "structure", "result": result_dict}]}
    except Exception as e:
        logger.exception("Structure Agent failed")
        await push_event(job_id, {"event": "agent_error", "agent": "structure", "message": f"Structure Agent error: {str(e)}"})
        return {"agent_outputs": [{"agent_name": "structure", "result": {"error": str(e)}}]}

async def character_node(state: PipelineState) -> Dict[str, Any]:
    """Execute Character Agent (staggered by 1.5s to respect TPM token rates)."""
    await asyncio.sleep(1.5)
    job_id = state["job_id"]
    logger.info("Executing Character Agent node for job: %s", job_id)
    await push_event(job_id, {"event": "agent_start", "agent": "character", "message": "Character Agent tracking motivations and arcs..."})
    
    try:
        # Cap at 80,000 chars to prevent OOM on free-tier hosting
        text = state["script_text"][:80000] if len(state["script_text"]) > 80000 else state["script_text"]
        res = await run_character_agent(text, state["page_count"])
        result_dict = res.model_dump()
        await push_event(job_id, {
            "event": "agent_complete", 
            "agent": "character", 
            "message": "Character Agent analysis complete.",
            "data": result_dict
        })
        return {"agent_outputs": [{"agent_name": "character", "result": result_dict}]}
    except Exception as e:
        logger.exception("Character Agent failed")
        await push_event(job_id, {"event": "agent_error", "agent": "character", "message": f"Character Agent error: {str(e)}"})
        return {"agent_outputs": [{"agent_name": "character", "result": {"error": str(e)}}]}

async def comps_node(state: PipelineState) -> Dict[str, Any]:
    """Execute Comps/Marketability Agent (staggered by 3.0s & text windowed)."""
    await asyncio.sleep(3.0)
    job_id = state["job_id"]
    logger.info("Executing Comps Agent node for job: %s", job_id)
    await push_event(job_id, {"event": "agent_start", "agent": "comps", "message": "Comps Agent querying TMDB and positioning..."})
    
    try:
        # Genre & tone extraction only requires the first 40,000 characters (approx. 20-25 pages)
        sample_text = state["script_text"][:40000] if len(state["script_text"]) > 40000 else state["script_text"]
        res = await run_comps_agent(sample_text, state["page_count"])
        result_dict = res.model_dump()
        await push_event(job_id, {
            "event": "agent_complete", 
            "agent": "comps", 
            "message": "Comps Agent analysis complete.",
            "data": result_dict
        })
        return {"agent_outputs": [{"agent_name": "comps", "result": result_dict}]}
    except Exception as e:
        logger.exception("Comps Agent failed")
        await push_event(job_id, {"event": "agent_error", "agent": "comps", "message": f"Comps Agent error: {str(e)}"})
        return {"agent_outputs": [{"agent_name": "comps", "result": {"error": str(e)}}]}

async def continuity_node(state: PipelineState) -> Dict[str, Any]:
    """Execute Continuity Agent (staggered by 4.5s)."""
    await asyncio.sleep(4.5)
    job_id = state["job_id"]
    logger.info("Executing Continuity Agent node for job: %s", job_id)
    await push_event(job_id, {"event": "agent_start", "agent": "continuity", "message": "Continuity Agent checking for contradictions..."})
    
    try:
        # Cap at 100,000 chars — continuity needs more context to catch contradictions
        text = state["script_text"][:100000] if len(state["script_text"]) > 100000 else state["script_text"]
        res = await run_continuity_agent(text, state["page_count"])
        result_dict = res.model_dump()
        await push_event(job_id, {
            "event": "agent_complete", 
            "agent": "continuity", 
            "message": "Continuity Agent analysis complete.",
            "data": result_dict
        })
        return {"agent_outputs": [{"agent_name": "continuity", "result": result_dict}]}
    except Exception as e:
        logger.exception("Continuity Agent failed")
        await push_event(job_id, {"event": "agent_error", "agent": "continuity", "message": f"Continuity Agent error: {str(e)}"})
        return {"agent_outputs": [{"agent_name": "continuity", "result": {"error": str(e)}}]}

async def synthesizer_node(state: PipelineState) -> Dict[str, Any]:
    """Execute Synthesizer Agent to compile everything into the final report."""
    job_id = state["job_id"]
    logger.info("Executing Synthesizer Agent node for job: %s", job_id)
    await push_event(job_id, {"event": "agent_start", "agent": "synthesizer", "message": "Synthesizer Agent compiling final coverage report..."})

    # Extract the individual agent outputs from the state
    structure_data = {}
    character_data = {}
    comps_data = {}
    continuity_data = {}

    for out in state["agent_outputs"]:
        name = out["agent_name"]
        res = out["result"]
        if name == "structure":
            structure_data = res
        elif name == "character":
            character_data = res
        elif name == "comps":
            comps_data = res
        elif name == "continuity":
            continuity_data = res

    try:
        report = await run_synthesizer_agent(
            state["page_count"],
            structure_data,
            character_data,
            comps_data,
            continuity_data
        )
        report_dict = report.model_dump()
        
        await push_event(job_id, {
            "event": "complete",
            "agent": "synthesizer",
            "message": "Coverage report synthesis complete.",
            "data": report_dict
        })
        return {"report": report_dict}
    except Exception as e:
        logger.exception("Synthesizer Agent failed")
        await push_event(job_id, {"event": "error", "agent": "synthesizer", "message": f"Synthesis error: {str(e)}"})
        raise e

# ── Build the Graph ────────────────────────────────────────────────────────

workflow = StateGraph(PipelineState)

# Add Nodes
workflow.add_node("structure", structure_node)
workflow.add_node("character", character_node)
workflow.add_node("comps", comps_node)
workflow.add_node("continuity", continuity_node)
workflow.add_node("synthesizer", synthesizer_node)

# Fan-out from START to analysis nodes
workflow.add_edge(START, "structure")
workflow.add_edge(START, "character")
workflow.add_edge(START, "comps")
workflow.add_edge(START, "continuity")

# Fan-in from analysis nodes to synthesizer
workflow.add_edge("structure", "synthesizer")
workflow.add_edge("character", "synthesizer")
workflow.add_edge("comps", "synthesizer")
workflow.add_edge("continuity", "synthesizer")

# Finish after synthesizer
workflow.add_edge("synthesizer", END)

# Compile
compiled_graph = workflow.compile()


def build_pipeline():
    """Return the pre-compiled LangGraph pipeline.

    The graph is compiled once at module import time. This factory function
    exists so callers can do ``from graph.pipeline import build_pipeline``
    and get the compiled graph via ``build_pipeline()``.
    """
    return compiled_graph


__all__ = ["compiled_graph", "build_pipeline"]
