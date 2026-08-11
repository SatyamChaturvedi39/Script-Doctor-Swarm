<div align="center">

# 🎬 Script Doctor Swarm

### Professional screenplay coverage, automated by a multi-agent LLM pipeline.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-FF6B35?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini_Flash-Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**[Live Demo](https://script-doctor-swarm.vercel.app)**

</div>

---

## What Is Script Coverage?

In the film industry, every screenplay submitted to a studio, production company, or agency passes through a **story analyst** (called a "reader") before it reaches a producer's desk. The reader produces a **coverage report** — a structured written evaluation containing:

- A **logline** — one-sentence premise
- A **synopsis** — brief narrative summary
- **Per-category ratings** — Structure, Character, Dialogue, Marketability, Continuity
- A **Pass / Consider / Recommend verdict** with written justification

Coverage is Hollywood's first filter. Script Doctor Swarm replicates this workflow end-to-end using five specialized LLM agents orchestrated by LangGraph, delivered through a real-time streaming API, and presented in a React UI styled as a physical studio reader's folder.

---

## Architecture

```
                         ┌─────────────────────────────────────┐
                         │       Script Doctor Swarm Pipeline   │
                         └──────────────┬──────────────────────┘
                                        │
                    ┌───────────────────▼────────────────────┐
                    │   Parser (pdfplumber / plain text)      │
                    │   Extracts text + inserts PAGE markers  │
                    └───────────────────┬────────────────────┘
                                        │ script_text
                         ┌──────────────▼──────────────┐
                         │     LangGraph StateGraph     │
                         │     (fan-out → fan-in)        │
                         └──┬──────┬──────┬──────┬──────┘
                            │      │      │      │   parallel execution
              ┌─────────────▼─┐ ┌──▼──┐ ┌▼────┐ ┌▼──────────────┐
              │  Structure    │ │Char-│ │Comps│ │  Continuity   │
              │  Agent        │ │acter│ │Agent│ │  Agent        │
              │  (Save the    │ │Agent│ │(TMDB│ │  (fact/prop   │
              │  Cat beats)   │ │     │ │RAG) │ │  contradicts) │
              └──────┬────────┘ └──┬──┘ └──┬──┘ └──────┬────────┘
                     │             │       │             │
                     └─────────────▼───────▼─────────────┘
                                          │
                              ┌───────────▼───────────┐
                              │   Synthesizer Agent    │
                              │   (final report +      │
                              │    verdict synthesis)  │
                              └───────────┬────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │     CoverageReport      │
                              │  (SSE → React frontend) │
                              └────────────────────────┘
```

### The Five Agents

| Agent | Task | Key Technique |
|---|---|---|
| **Structure Agent** | Locates 7 Save the Cat beats and measures % deviation from canonical page positions | Zero-shot prompting + deterministic Python math |
| **Character Agent** | Profiles character arcs and flags trait inconsistencies with page citations | Role-based prompting + structured JSON output |
| **Comps Agent** | Suggests real comparable films for market positioning | **3-Phase RAG**: keyword extraction → live TMDB API → grounded generation |
| **Continuity Agent** | Cross-references props, names, locations, and timelines for internal contradictions | Canary-injection evaluation methodology |
| **Synthesizer Agent** | Merges all four reports into the final logline, synopsis, scorecard, and verdict | Structured output constraints + hallucination guard |

### Key Engineering Decisions

- **Parallel fan-out** — The four analysis agents execute concurrently via LangGraph's `START` edge fan-out, cutting wall-clock pipeline time by ~75% vs. sequential execution.
- **RAG-grounded comps** — The Comps Agent queries TMDB _before_ generating any output. The synthesizer's system prompt explicitly forbids referencing films not present in the retrieved results, eliminating hallucinated comparable titles.
- **Smart text sampling** — For large screenplays, the Structure Agent receives 7 evenly-spaced chunks spanning the full script (rather than a simple head-truncation) so all beats remain detectable regardless of script length.
- **Multi-tier model cascade** — On Gemini API rate limits (`429 RESOURCE_EXHAUSTED`), the system automatically cascades through configured fallback models (`gemini-3.5-flash` → `gemini-3.5-flash-lite`) before sleeping.
- **Real-time SSE streaming** — FastAPI pushes `agent_start` / `agent_complete` events over Server-Sent Events as each agent finishes. The frontend shows a live progress tracker — users see partial results as the pipeline runs.
- **Temperature by task type** — Factual agents (Structure `0.1`, Continuity `0.1`) use near-deterministic decoding. Creative writing agents (Synthesizer `0.3`, Comps `0.3`) use measured sampling for natural prose.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini Flash (via `langchain-google-genai`) |
| **Agent Orchestration** | LangGraph `StateGraph` (parallel fan-out / fan-in DAG) |
| **Backend API** | FastAPI + Uvicorn |
| **Real-time Streaming** | Server-Sent Events (`sse-starlette`) |
| **TMDB Client** | `httpx` (async, with exponential backoff retry) |
| **PDF Parsing** | `pdfplumber` (layout-preserving extraction) |
| **Frontend** | React 18 + Vite + Tailwind CSS v4 |
| **Deployment** | Vercel (frontend) + Render (backend) |

---

## Repository Structure

```
Script-Doctor-Swarm/
├── backend/
│   ├── main.py                    # FastAPI app entry + CORS configuration
│   ├── config.py                  # Settings, API key pool, model cascade
│   ├── requirements.txt
│   ├── agents/
│   │   ├── base.py                # LLM factory, retry/failover logic, JSON parser
│   │   ├── structure_agent.py     # Save the Cat beat detection
│   │   ├── character_agent.py     # Arc profiling + inconsistency detection
│   │   ├── comps_agent.py         # TMDB-grounded comparable films (RAG)
│   │   ├── continuity_agent.py    # Prop / timeline / fact continuity
│   │   └── synthesizer_agent.py   # Final report synthesis + hallucination guard
│   ├── api/
│   │   ├── router.py              # POST /api/coverage, GET /stream, GET /{id}
│   │   ├── schemas.py             # Pydantic models for all agents and report
│   │   └── jobs.py                # In-memory job store with asyncio.Queue
│   ├── graph/
│   │   ├── pipeline.py            # LangGraph StateGraph + smart text sampling
│   │   ├── runner.py              # ainvoke wrapper + job store updates
│   │   └── state.py               # PipelineState TypedDict
│   ├── parser/
│   │   └── extractor.py           # PDF/TXT extraction + page-marker insertion
│   └── services/
│       └── tmdb_client.py         # 3-tier TMDB search (genre IDs → keyword IDs → text)
│
├── eval/
│   ├── run_eval.py                # Evaluation harness entry point
│   ├── structure_eval.py          # Beat detection accuracy (mean % deviation)
│   ├── character_eval.py          # Inconsistency detection (Precision / Recall / F1)
│   ├── comps_eval.py              # Comp relevance (overlap % vs. trade-press reference)
│   ├── continuity_eval.py         # Error detection recall (canary injection method)
│   ├── report_generator.py        # Formats results to JSON + Markdown
│   └── data/
│       ├── canary_scripts/        # Real scripts with injected ground-truth errors
│       ├── beat_sheets/           # Published beat-sheet answer keys
│       └── comps_reference/       # Trade-press comparable film references
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── App.jsx                # Root: UploadForm → ProgressTracker → CoverageReport
        ├── index.css              # Design tokens (paper/ink palette, typography)
        ├── api/client.js          # fetch() wrapper for /api/coverage
        ├── hooks/useSSE.js        # SSE consumer hook (EventSource)
        └── components/
            ├── UploadForm.jsx      # Drag-and-drop screenplay submission
            ├── ProgressTracker.jsx # Live agent status board (SSE-driven)
            ├── CoverageReport.jsx  # Final coverage sheet
            ├── VerdictStamp.jsx    # Animated rubber-stamp verdict
            ├── AgentTabs.jsx       # Tab navigation (Structure / Character / Comps / Continuity)
            ├── StructureDetail.jsx # Beat timeline table + supporting evidence
            ├── CharacterDetail.jsx # Character profiles + inconsistency flags
            ├── CompsDetail.jsx     # TMDB comp cards + market positioning
            └── ContinuityDetail.jsx # Continuity error log with page citations
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Google AI Studio](https://aistudio.google.com/) API key
- [TMDB API](https://www.themoviedb.org/settings/api) key (free tier, ~40 req/10s)

### 1. Clone and configure

```bash
git clone https://github.com/SatyamChaturvedi39/Script-Doctor-Swarm.git
cd Script-Doctor-Swarm
cp backend/.env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_key_here
TMDB_API_KEY=your_tmdb_key_here
GEMINI_MODEL=gemini-2.0-flash
FRONTEND_ORIGIN=http://localhost:5173

# Optional: fallback models on quota exhaustion
GEMINI_MODEL_FALLBACK=gemini-1.5-flash
GEMINI_MODEL_FALLBACK_TWO=gemini-1.5-flash-lite
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000` · Interactive docs: `http://localhost:8000/docs`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`

---

## API Reference

### `POST /api/coverage`

Upload a `.pdf` or `.txt` screenplay to start a coverage job.

**Request:** `multipart/form-data`, field `file`

**Response:**
```json
{ "job_id": "550e8400-e29b-41d4-a716-446655440000" }
```

---

### `GET /api/coverage/{job_id}/stream`

Server-Sent Events stream of live pipeline progress.

```jsonc
// Agent has started
{ "event": "agent_start",    "agent": "structure",  "message": "Analyzing beats..." }

// Agent finished — data contains structured output
{ "event": "agent_complete", "agent": "character",  "message": "Analysis complete", "data": { ... } }

// All agents done — data is the full CoverageReport
{ "event": "complete",       "agent": "synthesizer", "message": "Coverage complete", "data": { ... } }

// Pipeline error
{ "event": "error",          "agent": null,          "message": "Error description" }
```

---

### `GET /api/coverage/{job_id}`

Poll for the completed report (HTTP polling fallback).

| Status Code | Meaning |
|---|---|
| `202` | Pipeline still running |
| `200` | Complete — body contains `report` |
| `404` | Job not found |

---

## Coverage Report Schema

```typescript
interface CoverageReport {
  title: string;
  writer: string;
  genre: string;
  page_count: number;
  logline: string;
  synopsis: string;
  comments: {
    structure: string;
    character: string;
    dialogue: string;
    marketability: string;
    continuity: string;
  };
  scorecard: Array<{
    category: string;
    rating: "Excellent" | "Good" | "Fair" | "Poor";
  }>;
  verdict: "PASS" | "CONSIDER" | "RECOMMEND";
  verdict_justification: string;

  // Detailed agent output (powers the tabbed views in the UI)
  structure_detail: StructureResult;   // beats[], mean_deviation, assessment
  character_detail: CharacterResult;   // characters[], inconsistencies[]
  comps_detail: CompsResult;           // comparable_films[], positioning
  continuity_detail: ContinuityResult; // issues[], summary
}
```

---

## Evaluation Harness

The `eval/` directory contains a fully automated test harness. All evaluation uses **real screenplays and independently published reference data** — never self-generated test answers.

### Methodology by Agent

| Agent | Metric | Ground Truth Source |
|---|---|---|
| **Structure** | Mean Absolute % Deviation from expected beat positions | Published beat-sheet breakdowns (Get Out, Whiplash, Parasite) |
| **Character** | Precision / Recall / F1 on inconsistency detection | Canary injection — real scripts with deliberately planted contradictions |
| **Comps** | Overlap % vs. reference comparable films | Trade-press comparable film records |
| **Continuity** | Precision / Recall / F1 on error detection | Canary injection — real scripts with planted continuity errors |

### Results

- **Structure Agent**: 3.5–4.8% mean beat deviation across test scripts (all citations backed by direct page quotes)
- **Character Agent**: Precision 0.80 · Recall 0.75 · F1 0.77 on canary scripts
- **Comps Agent**: 60%+ genre/keyword overlap with trade-press comparable film references

### Run the harness

```bash
cd backend
python ../eval/run_eval.py
```

Results are written to `eval/results/eval_report_latest.md`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key (primary) |
| `TMDB_API_KEY` | ✅ Yes | TMDB v3 API key for comparable film lookup |
| `GEMINI_MODEL` | No | Primary model (default: `gemini-2.0-flash`) |
| `GEMINI_MODEL_FALLBACK` | No | Fallback on quota exhaustion |
| `GEMINI_MODEL_FALLBACK_TWO` | No | Second fallback |
| `GEMINI_API_KEY_FALLBACK` | No | Comma-separated additional API keys for rotation |
| `FRONTEND_ORIGIN` | No | Production frontend URL for CORS (default: `http://localhost:5173`) |

---

## Design Philosophy

The UI deliberately avoids generic AI-dashboard aesthetics. The visual experience is grounded in what a script coverage report *actually is* as a physical object — a studio reader's coverage folder.

| Design Token | Value | Purpose |
|---|---|---|
| `--color-paper` | `#F7F3E8` | Aged document cream |
| `--color-ink` | `#1F1B16` | Dark warm near-black |
| `--color-manila` | `#D4A847` | Classic manila folder yellow |
| `--color-red-flag` | `#C8302A` | Reader's correction red |
| `--color-carbon-blue` | `#1E3A5F` | Carbon copy blue |
| Font (headings) | `Courier Prime` | Typewriter authenticity |
| Font (body/UI) | `DM Sans` | Legible modern grotesque |

The **verdict stamp** (PASS / CONSIDER / RECOMMEND) is the only animated element — a rubber-stamp drop with rotation and opacity — designed to read as a physical evaluation artifact, not a UI widget.

---

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for full step-by-step instructions to deploy on:
- **Frontend** → Vercel (zero-config, auto-deploy from GitHub)
- **Backend** → Render (Python web service, free tier)

**Environment variables** must be set in both Vercel (for `VITE_API_BASE_URL`) and Render (for all backend secrets).

---


<div align="center">

*Built as a portfolio project demonstrating multi-agent LLM orchestration, RAG architecture, async Python backend engineering, and professional frontend UI design.*

</div>
