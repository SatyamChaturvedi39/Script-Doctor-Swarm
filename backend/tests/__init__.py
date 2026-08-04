"""
Backend test suite for Script Doctor Swarm.

Tests are organized by component:
  - test_parser.py       — screenplay text extraction
  - test_agents.py       — per-agent unit tests with mocked LLM
  - test_api.py          — FastAPI endpoint integration tests
  - test_pipeline.py     — LangGraph pipeline integration tests

Run with:
  cd backend
  pytest tests/ -v
"""
