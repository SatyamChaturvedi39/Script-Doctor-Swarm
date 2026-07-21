# Script Doctor Swarm

> **Professional screenplay coverage, automated.**
> A multi-agent LLM system that produces industry-standard script coverage reports — logline, synopsis, scorecard, and a Pass / Consider / Recommend verdict — by running five specialized LangGraph agents in parallel over a screenplay PDF or text file.

---

## What Is Script Coverage?

Script coverage is the studio reader's written evaluation of a screenplay before it reaches a producer's desk. A standard coverage report includes:

- A **logline** (one-sentence premise)
- A **synopsis** (brief narrative summary)
- **Category ratings** (Structure, Character, Dialogue, Concept, Marketability)
- A **Pass / Consider / Recommend** verdict with written justification

Coverage is the gatekeeper of Hollywood development. Script Doctor Swarm replicates the full coverage workflow using five purpose-built LLM agents coordinated by LangGraph, served through a FastAPI backend, and displayed in a React frontend styled to look like a physical studio reader's folder.

---

## Architecture

```
+-----------------------------------------------------------------------+
|                         LangGraph Pipeline                            |
|                                                                       |
|   Screenplay Text                                                     |
|        |                                                              |
|        v                                                              |
|   +---------+        +---------------+  +---------------+            |
|   | Parser  |------> | Structure Agt |  | Character Agt |            |
|   | (PDF/   |        +-------+-------+  +-------+-------+            |
|   |  TXT)   |                |   (fan-out)       |                   |
|   +---------+        +-------+-------+  +-------+-------+            |
|                       |  Comps Agt   |  |Continuity Agt |            |
|                       | (TMDB API)   |  |               |            |
|                       +-------+-------+  +-------+-------+            |
|                               |   (fan-in)        |                   |
|                               +--------+----------+                   |
|                                        v                              |
|                               +-----------------+                     |
|                               |  Synthesizer Agt |                    |
|                               |  (Gemini Flash)  |                    |
|                               +--------+--------+                     |
|                                        |                              |
|                                   CoverageReport                      |
+-----------------------------------------------------------------------+
```

### Agent Responsibilities

| Agent | Role |
|---|---|
| **Structure Agent** | Detects the 7 Save the Cat beats and measures deviation from their canonical page-percentage positions |
| **Character Agent** | Profiles each character's arc, stated motivation, and flags trait inconsistencies with no narrative justification |
| **Comps / Marketability Agent** | Queries TMDB _before_ generating any text; all comparable films are grounded in retrieved search results, never hallucinated |
| **Continuity Agent** | Cross-references props, timelines, established facts, and locations for internal contradictions |
| **Synthesizer Agent** | Reads all four agent reports and produces the final logline, synopsis, scorecard ratings, verdict, and written justification |

### Key Design Decisions

- **Parallel fan-out**: The four analysis agents run concurrently via LangGraph's `Send` API, cutting wall-clock time by ~75% versus sequential execution.
- **LangGraph `Annotated[list, operator.add]`**: Parallel agents safely append results into a shared list without race conditions.
- **No hallucinated comps**: The Comps Agent receives only TMDB JSON as context — the system prompt forbids referencing any film not present in the retrieved results.
- **SSE streaming**: The FastAPI backend pushes real-time `agent_start` / `agent_complete` events over Server-Sent Events so the frontend shows a live progress tracker as each agent finishes.
- **Gemini 2.0 Flash**: Every agent uses `gemini-2.0-flash` for speed and cost efficiency. Each agent enforces `response_mime_type: "application/json"` to avoid unstructured output.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 2.0 Flash (`google-generativeai`) |
| **Orchestration** | LangGraph (StateGraph, fan-out/fan-in) |
| **Backend API** | FastAPI + Uvicorn |
| **TMDB Client** | httpx (async) |
| **PDF Parsing** | PyMuPDF (`fitz`) |
| **Frontend** | React + Vite + Tailwind CSS v4 |
| **Streaming** | Server-Sent Events (SSE) |

---

## Repository Structure

```
Script-Doctor-Swarm/
+-- backend/
|   +-- main.py                    # FastAPI application entry point
|   +-- config.py                  # Settings (API keys, TMDB base URL)
|   +-- requirements.txt
|   +-- agents/
|   |   +-- structure_agent.py     # Save the Cat beat detection
|   |   +-- character_agent.py     # Arc profiling + inconsistency detection
|   |   +-- comps_agent.py         # TMDB-grounded comparable films
|   |   +-- continuity_agent.py    # Prop / timeline / fact continuity
|   |   \-- synthesizer_agent.py   # Final report synthesis
|   +-- api/
|   |   +-- router.py              # /api/coverage routes + SSE endpoint
|   |   +-- schemas.py             # Pydantic models (all agents + report)
|   |   \-- jobs.py                # In-memory job store with asyncio.Queue
|   +-- graph/
|   |   +-- pipeline.py            # LangGraph StateGraph definition
|   |   \-- runner.py              # ainvoke wrapper + SSE event emission
|   +-- parser/
|   |   \-- extractor.py           # PDF/TXT extraction + page count estimate
|   \-- services/
|       \-- tmdb_client.py         # Async TMDB search client
|
+-- eval/
|   +-- run_eval.py                # Automated evaluation harness entry point
|   +-- report_generator.py        # Formats eval results to JSON + Markdown
|   +-- generate_mock_scripts.py   # Generates synthetic test screenplays
|   +-- structure_eval.py          # Beat detection scoring vs. answer keys
|   +-- character_eval.py          # Arc + inconsistency detection scoring
|   +-- comps_eval.py              # TMDB comp relevance scoring
|   +-- continuity_eval.py         # Error detection recall scoring
|   \-- data/
|       +-- mock_scripts/          # Synthetic test screenplays
|       +-- beat_answer_keys/      # Ground-truth beat positions
|       \-- comps_reference/       # Reference comparable films
|
\-- frontend/
    +-- index.html
    +-- vite.config.js
    \-- src/
        +-- App.jsx                # Root: UploadForm -> ProgressTracker -> CoverageReport
        +-- index.css              # Design tokens (paper/ink palette, Courier/Grotesk fonts)
        +-- api/
        |   \-- client.js          # Axios client for /api/coverage
        +-- hooks/
        |   \-- useSSE.js          # SSE consumer hook
        \-- components/
            +-- UploadForm.jsx      # Drag-and-drop file upload
            +-- ProgressTracker.jsx # Live agent status board
            +-- CoverageReport.jsx  # Final coverage sheet
            +-- VerdictStamp.jsx    # Animated rubber-stamp verdict
            +-- AgentTabs.jsx       # Tab navigation for detail views
            +-- StructureDetail.jsx # Beat timeline visualization
            +-- CharacterDetail.jsx # Character profiles + inconsistencies
            +-- CompsDetail.jsx     # TMDB comp cards + positioning
            \-- ContinuityDetail.jsx # Continuity error log
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini 2.0 Flash)
- A [TMDB API](https://www.themoviedb.org/settings/api) read-access token

### 1. Clone and configure

```bash
git clone https://github.com/SatyamChaturvedi39/Script-Doctor-Swarm.git
cd Script-Doctor-Swarm
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY and TMDB_API_KEY
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## API Reference

### `POST /api/coverage`

Upload a screenplay file (`.pdf` or `.txt`) to start a coverage job.

**Request:** `multipart/form-data` with field `file`.

**Response:**
```json
{ "job_id": "uuid-string" }
```

---

### `GET /api/coverage/{job_id}/stream`

Server-Sent Events stream. Each event is a JSON-encoded `AgentProgressEvent`:

```jsonc
// Agent has started processing
{ "event": "agent_start", "agent": "structure", "message": "Analyzing beats..." }

// Agent finished
{ "event": "agent_complete", "agent": "character", "message": "Character analysis complete", "data": { ... } }

// All agents done — data contains the full CoverageReport
{ "event": "complete", "agent": null, "message": "Coverage complete", "data": { ... } }

// Something went wrong
{ "event": "error", "agent": null, "message": "Error description" }
```

---

### `GET /api/coverage/{job_id}`

Poll the job status synchronously (for cases where SSE is unavailable).

**Response:**
```json
{
  "job_id": "...",
  "status": "complete",
  "report": { ... }
}
```

---

## Coverage Report Schema

```typescript
{
  title: string;
  writer: string;
  genre: string;
  page_count: number;
  logline: string;
  synopsis: string;
  comments: { [category: string]: string };
  scorecard: Array<{ category: string; rating: "Excellent" | "Good" | "Fair" | "Poor" }>;
  verdict: "PASS" | "CONSIDER" | "RECOMMEND";
  verdict_justification: string;

  // Detailed agent output (powers the tabbed views in the UI)
  structure_detail: StructureResult;
  character_detail: CharacterResult;
  comps_detail: CompsResult;
  continuity_detail: ContinuityResult;
}
```

---

## Evaluation Harness

The `eval/` directory contains a fully automated test harness that:

1. Generates **synthetic test screenplays** modeled on *The Dark Knight*, *Get Out*, and *Jaws*.
2. Runs each agent against the test scripts and compares output against **ground-truth answer keys**.
3. Scores each agent on precision/recall metrics appropriate to its task:
   - **Structure Agent**: Beat detection accuracy (within ±5% page tolerance)
   - **Character Agent**: Named character recall + inconsistency detection recall
   - **Comps Agent**: Comp relevance score (genre/keyword overlap with reference films)
   - **Continuity Agent**: Error detection recall against seeded continuity bugs
4. Outputs a full **JSON + Markdown report** to `eval/results/`.

**Run the harness:**
```bash
cd backend
python ../eval/run_eval.py
```

---

## Design Philosophy

The UI deliberately avoids generic AI-dashboard aesthetics. The experience is grounded in what a script coverage report *actually is* as a physical object — a studio reader's coverage folder.

**Design tokens:**

| Token | Value | Purpose |
|---|---|---|
| `--color-paper` | `#F7F3E8` | Aged document cream |
| `--color-ink` | `#1F1B16` | Dark warm near-black |
| `--color-red-flag` | `#C8302A` | Reader's correction red |
| Font (headings/labels) | `Courier Prime` | Typewriter authenticity |
| Font (body/UI) | `DM Sans` | Legible modern grotesque |

The **verdict stamp** (PASS / CONSIDER / RECOMMEND) is the only animated element — a rubber-stamp drop with rotation + opacity transition — so it reads as a physical evaluation artifact rather than a UI widget.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI Studio key for Gemini 2.0 Flash |
| `TMDB_API_KEY` | Yes | TMDB read-access token for comparable film lookup |

See [`.env.example`](.env.example) for the template.

---

## License

MIT. See [LICENSE](LICENSE) for details.

---

*Built as a portfolio project demonstrating multi-agent LLM orchestration, async Python backends, and professional frontend UI design.*
