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
    """Extract from PDF using pdfplumber with layout preservation."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "pdfplumber is required for PDF support. "
            "Install it with: pip install pdfplumber"
        )

    pages_text: list[str] = []
    buf = io.BytesIO(raw_bytes)

    with pdfplumber.open(buf) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""
            pages_text.append(f"\n--- PAGE {i} ---\n{text}")

    result = "\n".join(pages_text)
    logger.info("Extracted %d pages from PDF", len(pages_text))
    return result


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
