"""
Script Doctor Swarm — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.router import router as api_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("script_doctor")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Script Doctor Swarm backend starting")
    logger.info("Gemini model: %s", settings.GEMINI_MODEL)
    logger.info("CORS origin : %s", settings.FRONTEND_ORIGIN)
    yield
    logger.info("Script Doctor Swarm backend shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Script Doctor Swarm",
    description="Multi-agent screenplay coverage system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Vite dev server + production frontend (including all Vercel subdomains)
settings = get_settings()

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if settings.FRONTEND_ORIGIN:
    for o in settings.FRONTEND_ORIGIN.split(","):
        o_clean = o.strip().rstrip("/")
        if o_clean and o_clean not in allowed_origins:
            allowed_origins.append(o_clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Automatically allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "script-doctor-swarm"}
