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
    GEMINI_API_KEY_FALLBACK: str = ""
    TMDB_API_KEY: str = ""

    # --- Model Configuration ---
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_MODEL_FALLBACK: str = "gemini-3.5-flash"
    GEMINI_MODEL_FALLBACK_TWO: str = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODEL: str = ""  # alias for backward compatibility

    # --- TMDB ---
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w300"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    def get_api_key_pool(self) -> list[str]:
        """
        Return a list of available Gemini API keys for rotation/failover.
        """
        keys: list[str] = []
        if self.GEMINI_API_KEY:
            for k in self.GEMINI_API_KEY.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)
        if self.GEMINI_API_KEY_FALLBACK:
            for k in self.GEMINI_API_KEY_FALLBACK.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)
        return keys or [""]

    def get_model_cascade(self) -> list[str]:
        """
        Return an ordered list of fallback models to try sequentially upon 429 quota exhaustion.
        """
        cascade: list[str] = []
        candidates = [
            self.GEMINI_MODEL,
            self.GEMINI_MODEL_FALLBACK,
            self.GEMINI_MODEL_FALLBACK_TWO,
            self.GEMINI_FALLBACK_MODEL,
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
        ]
        for m in candidates:
            m_clean = m.strip() if m else ""
            if m_clean and m_clean not in cascade:
                cascade.append(m_clean)
        return cascade

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
