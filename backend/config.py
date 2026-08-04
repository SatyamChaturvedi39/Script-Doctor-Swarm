"""
Configuration management for Script Doctor Swarm backend.
Reads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


import os
from dotenv import load_dotenv

# Load .env from project root or current working directory
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- API Keys ---
    GEMINI_API_KEY: str = ""
    TMDB_API_KEY: str = ""

    # --- Model Configuration ---
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # --- TMDB ---
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w300"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
