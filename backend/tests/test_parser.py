"""
Tests for backend/parser/extractor.py

Run from the backend/ directory:
  pytest tests/test_parser.py -v
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.extractor import extract_text, estimate_page_count, LINES_PER_PAGE


class TestExtractText:
    def test_txt_extraction_inserts_page_markers(self):
        """Plain text should get PAGE markers injected."""
        # 56 lines = exactly 1 page
        sample_txt = "\n".join([f"Line {i}" for i in range(LINES_PER_PAGE)])
        result = extract_text(sample_txt.encode("utf-8"), "test.txt")
        assert "--- PAGE 1 ---" in result

    def test_txt_extraction_multi_page(self):
        """Text longer than 56 lines should produce multiple page markers."""
        sample_txt = "\n".join([f"Line {i}" for i in range(LINES_PER_PAGE * 3)])
        result = extract_text(sample_txt.encode("utf-8"), "test.txt")
        assert "--- PAGE 1 ---" in result
        assert "--- PAGE 2 ---" in result
        assert "--- PAGE 3 ---" in result

    def test_txt_extraction_preserves_content(self):
        """Page content should survive extraction."""
        content = "FADE IN:\nINT. COFFEE SHOP - DAY\nSARAH stares at her phone."
        result = extract_text(content.encode("utf-8"), "script.txt")
        assert "FADE IN:" in result
        assert "INT. COFFEE SHOP" in result

    def test_extension_fallback_to_txt(self):
        """Files without extension should be treated as plain text."""
        content = "A short screenplay."
        result = extract_text(content.encode("utf-8"), "noextension")
        assert "A short screenplay." in result


class TestEstimatePageCount:
    def test_counts_page_markers(self):
        """Should count PAGE markers correctly."""
        text = "--- PAGE 1 ---\nContent\n--- PAGE 2 ---\nMore\n--- PAGE 5 ---\nEnd"
        assert estimate_page_count(text) == 5

    def test_fallback_to_line_heuristic(self):
        """Without PAGE markers, falls back to line count / 56."""
        text = "\n".join([f"Line {i}" for i in range(LINES_PER_PAGE * 3)])
        count = estimate_page_count(text)
        assert count == 3

    def test_minimum_of_1(self):
        """Even a single-line script should return at least 1 page."""
        assert estimate_page_count("just one line") >= 1
