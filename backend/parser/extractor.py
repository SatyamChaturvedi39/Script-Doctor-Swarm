"""
Script text extraction from .txt and .pdf files.

Preserves page boundaries as `--- PAGE N ---` markers so that
downstream agents can reference page positions.
"""

from __future__ import annotations

import io
import logging
import re

logger = logging.getLogger("script_doctor.parser")

# Standard screenplay formatting: ~56 lines per page
LINES_PER_PAGE = 56


def extract_text(raw_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a screenplay file.

    Supports:
      - .txt  — direct UTF-8 decode
      - .pdf  — pdfplumber with layout preservation

    Returns the full script text with page markers inserted.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(raw_bytes)
    else:
        return _extract_txt(raw_bytes)


def _extract_txt(raw_bytes: bytes) -> str:
    """Extract from plain text, inserting synthetic page markers."""
    text = raw_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()
    pages: list[str] = []
    page_num = 1

    for i in range(0, len(lines), LINES_PER_PAGE):
        chunk = "\n".join(lines[i : i + LINES_PER_PAGE])
        pages.append(f"\n--- PAGE {page_num} ---\n{chunk}")
        page_num += 1

    return "\n".join(pages)


def _extract_pdf(raw_bytes: bytes) -> str:
    """Extract from PDF using pypdf or pdfplumber with fast text extraction."""
    pages_text: list[str] = []
    buf = io.BytesIO(raw_bytes)

    # Try pypdf first if installed (much faster)
    try:
        import pypdf
        reader = pypdf.PdfReader(buf, strict=False)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"\n--- PAGE {i} ---\n{text}")
        result = "\n".join(pages_text)
        if result.strip():
            logger.info("Extracted %d pages from PDF using pypdf", len(pages_text))
            return result
    except Exception as e:
        logger.warning("pypdf extraction failed or yielded empty text: %s, trying pdfplumber", e)

    # Fallback to pdfplumber without layout=True (layout=True is 100x slower on 5MB+ PDFs and causes timeouts)
    try:
        import pdfplumber
        buf.seek(0)
        with pdfplumber.open(buf) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages_text.append(f"\n--- PAGE {i} ---\n{text}")
        result = "\n".join(pages_text)
        logger.info("Extracted %d pages from PDF using pdfplumber", len(pages_text))
        return result
    except Exception as e:
        logger.error("pdfplumber extraction failed: %s", e)
        raise RuntimeError(f"Could not extract text from PDF: {e}")


def estimate_page_count(script_text: str) -> int:
    """
    Count the number of pages in the extracted script text.

    Looks for `--- PAGE N ---` markers; falls back to line-count heuristic.
    """
    markers = re.findall(r"--- PAGE (\d+) ---", script_text)
    if markers:
        return max(int(m) for m in markers)

    # Fallback: estimate from line count
    line_count = len(script_text.splitlines())
    return max(1, round(line_count / LINES_PER_PAGE))


def extract_character_candidates(script_text: str) -> list[str]:
    """
    Extract candidate character names from script text.

    Handles:
      - Standard uppercase dialogue headers: `JOHNNY`, `DENNY (O.S.)`
      - Colon-style dialogue headers (transcripts/web scripts): `Johnny:`, `Claudette (18):`
      - Character introductions in action: `DENNY (18)`, `CLAUDETTE, 50`

    Returns a deduplicated list of character name strings ordered by frequency.
    """
    counts: dict[str, int] = {}
    lines = script_text.splitlines()

    # Words to ignore (technical screenplay terms & common English stop words)
    IGNORE = {
        "INT", "EXT", "DAY", "NIGHT", "FADE", "CUT", "SCENE", "PAGE", "THE",
        "CONTINUED", "TO", "IN", "ON", "AT", "BY", "WITH", "FROM", "AND", "OR",
        "BUT", "FOR", "O.S.", "V.O.", "CONT'D", "TITLE", "ANGLE", "CLOSE",
        "CAMERA", "VIEW", "SHOT", "FRAME", "BOYS", "GIRLS", "MAN", "WOMAN",
    }

    for line in lines:
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("--- PAGE"):
            continue

        candidate = None

        # Pattern 1: Colon style header ("Johnny:", "Claudette:", "DENNY (18):")
        colon_match = re.match(r"^([A-Za-z][A-Za-z0-9 '\-\.]{1,25})\s*:", cleaned)
        if colon_match:
            candidate = colon_match.group(1).strip()
            # Remove parentheticals inside name e.g. "Claudette (O.S.)" -> "Claudette"
            candidate = re.sub(r"\s*\(.*?\)", "", candidate).strip()

        # Pattern 2: Standard uppercase screenplay header ("JOHNNY", "MARK (V.O.)")
        elif re.match(r"^[A-Z][A-Z0-9 '\-\.]{1,25}(?:\s*\(.*?\))?$", cleaned):
            cand = re.sub(r"\s*\(.*?\)", "", cleaned).strip()
            if cand not in IGNORE and len(cand) >= 2 and not cand.startswith("INT.") and not cand.startswith("EXT."):
                candidate = cand

        # Pattern 3: Character introductions ("DENNY (18)", "CLAUDETTE (50s)")
        if not candidate:
            intro_matches = re.findall(r"\b([A-Z]{2,20})\s*\(\s*\d{1,2}[sS]?\s*\)", line)
            for m in intro_matches:
                if m not in IGNORE:
                    counts[m.title()] = counts.get(m.title(), 0) + 2

        if candidate:
            cand_norm = candidate.title()
            cand_upper = candidate.upper()
            if cand_upper not in IGNORE and len(cand_norm) >= 2:
                counts[cand_norm] = counts.get(cand_norm, 0) + 1

    # Sort by frequency descending and return top candidates
    sorted_candidates = [name for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True) if count >= 2]
    logger.info("Extracted %d candidate character names from text: %s", len(sorted_candidates), sorted_candidates[:10])
    return sorted_candidates[:15]

