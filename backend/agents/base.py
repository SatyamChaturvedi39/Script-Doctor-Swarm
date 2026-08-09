"""
Shared agent utilities.

Provides:
  - LLM instantiation with retry logic
  - Script chunking for context-window management
  - Structured output parsing from LLM responses
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Type

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger("script_doctor.agents")

# Maximum retries for rate-limited requests
MAX_RETRIES = 3
RETRY_BASE_DELAY = 15.0  # seconds; backoff: 15s → 30s → 60s  (matches Gemini free-tier Retry-After)


def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """
    Create a configured Gemini LLM instance.

    Uses the model specified in settings (default: gemini-2.5-flash).
    """
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
        max_retries=MAX_RETRIES,
    )


async def invoke_llm_with_retry(
    llm: ChatGoogleGenerativeAI,
    messages: list,
    max_retries: int = MAX_RETRIES,
) -> str:
    """
    Invoke the LLM with exponential backoff and automatic API key rotation on rate limits.

    Returns the raw string content of the response.

    Key Failover: If a key pool (comma-separated GEMINI_API_KEY or GEMINI_API_KEY_FALLBACK)
    is configured in settings, rate-limited requests automatically switch to the next key
    in the pool before waiting.
    """
    import asyncio
    import re
    from config import get_settings

    settings = get_settings()
    key_pool = settings.get_api_key_pool()
    model_cascade = settings.get_model_cascade()
    
    current_key_idx = 0
    current_model = getattr(llm, "model", settings.GEMINI_MODEL)
    current_model_idx = model_cascade.index(current_model) if current_model in model_cascade else 0

    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(messages)
            content = response.content
            # Coerce list-of-parts (new multimodal format) to plain string
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, str):
                        parts.append(part)
                    elif isinstance(part, dict):
                        parts.append(part.get("text", ""))
                content = "".join(parts)
            return str(content)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Failover Step 1: Try next API Key in key pool for current model
                if len(key_pool) > 1 and current_key_idx < len(key_pool) - 1:
                    current_key_idx += 1
                    next_key = key_pool[current_key_idx]
                    logger.warning(
                        "API Key quota exhausted (429). Failing over to key #%d (%s...) for model '%s'",
                        current_key_idx + 1, next_key[:8], current_model
                    )
                    llm = ChatGoogleGenerativeAI(
                        model=current_model,
                        google_api_key=next_key,
                        temperature=getattr(llm, "temperature", 0.2),
                        max_retries=1,
                    )
                    continue

                # Failover Step 2: Try next model in model cascade (e.g. 3.6-flash -> 3.5-flash -> 3.5-flash-lite)
                if current_model_idx < len(model_cascade) - 1:
                    current_model_idx += 1
                    current_key_idx = 0  # Reset to first key for new model
                    current_model = model_cascade[current_model_idx]
                    current_key = key_pool[current_key_idx] if key_pool else settings.GEMINI_API_KEY
                    logger.warning(
                        "Model quota exhausted (429). Advancing cascade to model #%d '%s'...",
                        current_model_idx + 1, current_model
                    )
                    llm = ChatGoogleGenerativeAI(
                        model=current_model,
                        google_api_key=current_key,
                        temperature=getattr(llm, "temperature", 0.2),
                        max_retries=1,
                    )
                    continue

                if attempt < max_retries:
                    retry_after_match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str, re.IGNORECASE)
                    if retry_after_match:
                        delay = float(retry_after_match.group(1)) + 2.0
                    else:
                        delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1, max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
            raise

    raise RuntimeError("Max retries exceeded")


def chunk_script(text: str, max_chars: int = 80_000) -> list[str]:
    """
    Split a long script into overlapping chunks for context-window management.

    Each chunk includes the full script header (first 2 pages) for context,
    plus a segment of the remaining text. Overlap ensures no beat or
    continuity issue falls between chunks.
    """
    if len(text) <= max_chars:
        return [text]

    # Find page markers
    pages = re.split(r"(--- PAGE \d+ ---)", text)

    # Reassemble pages as (marker, content) pairs
    segments: list[str] = []
    current = ""
    for part in pages:
        current += part
        if re.match(r"--- PAGE \d+ ---", part):
            if len(current) > 0:
                segments.append(current)
                current = ""
    if current.strip():
        segments.append(current)

    # Build chunks with overlap
    chunks: list[str] = []
    header = "\n".join(segments[:2]) if len(segments) > 2 else ""
    chunk_segments: list[str] = []
    chunk_size = 0

    overlap_segments = 2  # pages of overlap between chunks

    for seg in segments:
        chunk_segments.append(seg)
        chunk_size += len(seg)

        if chunk_size >= max_chars - len(header):
            chunk_text = header + "\n" + "\n".join(chunk_segments)
            chunks.append(chunk_text)
            # Keep overlap
            chunk_segments = chunk_segments[-overlap_segments:]
            chunk_size = sum(len(s) for s in chunk_segments)

    # Don't forget the last chunk
    if chunk_segments:
        chunk_text = header + "\n" + "\n".join(chunk_segments)
        if not chunks or chunk_text != chunks[-1]:
            chunks.append(chunk_text)

    logger.info("Script chunked into %d segments", len(chunks))
    return chunks


def parse_json_from_response(response) -> dict:
    """
    Extract a JSON object from an LLM response.

    Handles responses that include markdown code fences, extra text
    before/after the JSON, etc. Accepts str or list (defensive coercion).
    """
    # Defensive coercion — should already be str from invoke_llm_with_retry
    if not isinstance(response, str):
        if isinstance(response, list):
            parts = []
            for part in response:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    parts.append(part.get("text", ""))
            response = "".join(parts)
        else:
            response = str(response)

    # Try to find JSON in code fences first
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find a raw JSON object
    brace_match = re.search(r"\{.*\}", response, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: try the entire response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Could not parse JSON from LLM response: %s...", response[:200])
        return {}


def validate_output(data: dict, model_class: Type[BaseModel]) -> BaseModel:
    """Validate a dict against a Pydantic model, filling defaults for missing fields."""
    try:
        return model_class.model_validate(data)
    except Exception as e:
        logger.warning("Output validation partial failure: %s", e)
        # Try with lenient parsing
        return model_class.model_construct(**data)
