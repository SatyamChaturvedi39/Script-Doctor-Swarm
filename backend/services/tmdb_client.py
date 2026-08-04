"""
Async TMDB (The Movie Database) client.

Used exclusively by the Comps/Marketability Agent to retrieve real
comparable films. All comp suggestions MUST come from TMDB results,
never from LLM memory.

Rate limit: TMDB allows 40 requests per 10 seconds on the free tier.
All requests use exponential backoff retry on 429 / 5xx responses.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger("script_doctor.tmdb")

# Cache genre list for the lifetime of the process
_genre_cache: Optional[dict[str, int]] = None

# Retry config for TMDB rate limits
_TMDB_MAX_RETRIES = 4
_TMDB_RETRY_BASE_DELAY = 2.0  # seconds; doubles each attempt → 2, 4, 8, 16


async def _get_client() -> httpx.AsyncClient:
    """Create an httpx client with TMDB auth.

    TMDB supports two auth methods:
      - v3 API key: passed as ?api_key=... query parameter
      - v4 Bearer token: passed as Authorization: Bearer ... header

    The key in config is treated as a v3 API key (query param).
    This avoids the 401 that results from sending a v3 key as a Bearer token.
    """
    settings = get_settings()
    return httpx.AsyncClient(
        base_url=settings.TMDB_BASE_URL,
        params={"api_key": settings.TMDB_API_KEY},
        timeout=15.0,
    )



async def _tmdb_get_with_retry(client: httpx.AsyncClient, path: str, params: dict | None = None) -> httpx.Response:
    """
    GET a TMDB endpoint with exponential backoff on 429 / 5xx.

    Raises the last httpx.HTTPStatusError if all retries are exhausted.
    """
    resp = None
    for attempt in range(_TMDB_MAX_RETRIES + 1):
        resp = await client.get(path, params=params)
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < _TMDB_MAX_RETRIES:
                # Honour Retry-After header if present, otherwise exponential backoff
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else _TMDB_RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "TMDB %s on %s (attempt %d/%d), retrying in %.1fs",
                    resp.status_code, path, attempt + 1, _TMDB_MAX_RETRIES, delay,
                )
                await asyncio.sleep(delay)
                continue
        resp.raise_for_status()
        return resp
    assert resp is not None
    resp.raise_for_status()  # final raise
    return resp  # unreachable, satisfies type checker


async def get_genre_map() -> dict[str, int]:
    """
    Fetch the genre-name → genre-id mapping from TMDB.
    Cached after first call.
    """
    global _genre_cache
    if _genre_cache is not None:
        return _genre_cache

    async with await _get_client() as client:
        resp = await _tmdb_get_with_retry(client, "/genre/movie/list", params={"language": "en-US"})
        data = resp.json()

    _genre_cache = {g["name"].lower(): g["id"] for g in data.get("genres", [])}
    logger.info("Loaded %d TMDB genres", len(_genre_cache))
    return _genre_cache


async def search_keywords(query: str) -> list[dict]:
    """
    Search TMDB for keyword IDs matching a query string.

    Returns list of {id, name} dicts.
    """
    async with await _get_client() as client:
        resp = await _tmdb_get_with_retry(client, "/search/keyword", params={"query": query, "page": 1})
        results = resp.json().get("results", [])

    return [{"id": r["id"], "name": r["name"]} for r in results[:5]]


async def resolve_keyword_ids(keywords: list[str]) -> list[int]:
    """
    Resolve a list of keyword strings to TMDB keyword IDs.
    Returns the first match for each keyword.
    """
    ids: list[int] = []
    for kw in keywords[:8]:  # Limit to avoid rate issues
        results = await search_keywords(kw)
        if results:
            ids.append(results[0]["id"])
    return ids


async def resolve_genre_ids(genres: list[str]) -> list[int]:
    """Map genre name strings to TMDB genre IDs."""
    genre_map = await get_genre_map()
    ids: list[int] = []
    for g in genres:
        gid = genre_map.get(g.lower())
        if gid:
            ids.append(gid)
    return ids


async def discover_movies(
    genre_ids: list[int] | None = None,
    keyword_ids: list[int] | None = None,
    min_year: int = 2010,
    min_votes: int = 100,
    max_results: int = 10,
) -> list[dict]:
    """
    Discover movies from TMDB matching the given genre and keyword filters.

    Returns raw TMDB movie dicts with fields:
      id, title, release_date, genre_ids, overview, vote_average, poster_path
    """
    params: dict = {
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "vote_count.gte": str(min_votes),
        "primary_release_date.gte": f"{min_year}-01-01",
        "page": "1",
    }

    if genre_ids:
        params["with_genres"] = ",".join(str(g) for g in genre_ids)
    if keyword_ids:
        params["with_keywords"] = "|".join(str(k) for k in keyword_ids)

    async with await _get_client() as client:
        resp = await _tmdb_get_with_retry(client, "/discover/movie", params=params)
        data = resp.json()

    results = data.get("results", [])[:max_results]
    logger.info(
        "TMDB discover: %d results (genres=%s keywords=%s)",
        len(results),
        genre_ids,
        keyword_ids,
    )
    return results


async def get_movie_details(movie_id: int) -> dict:
    """Fetch detailed info for a single movie."""
    async with await _get_client() as client:
        resp = await _tmdb_get_with_retry(client, f"/movie/{movie_id}", params={"language": "en-US"})
        return resp.json()


async def find_comparable_films(
    genres: list[str],
    keywords: list[str],
    min_year: int = 2010,
    max_results: int = 5,
) -> list[dict]:
    """
    High-level function: resolve genres + keywords to IDs,
    then discover matching films.

    Returns a curated list of comparable films from TMDB.
    """
    genre_ids = await resolve_genre_ids(genres)
    keyword_ids = await resolve_keyword_ids(keywords)

    # Try with both genres and keywords first
    movies = await discover_movies(
        genre_ids=genre_ids,
        keyword_ids=keyword_ids,
        min_year=min_year,
        max_results=max_results * 2,  # fetch extra, then trim
    )

    # If too few results, fall back to genres only
    if len(movies) < 3 and genre_ids:
        logger.info("Few results with keywords, falling back to genre-only search")
        movies = await discover_movies(
            genre_ids=genre_ids,
            keyword_ids=None,
            min_year=min_year,
            max_results=max_results * 2,
        )

    # Resolve genre names for the results
    genre_map = await get_genre_map()
    id_to_name = {v: k.title() for k, v in genre_map.items()}

    formatted: list[dict] = []
    for m in movies[:max_results]:
        release_year = None
        if m.get("release_date"):
            try:
                release_year = int(m["release_date"][:4])
            except (ValueError, IndexError):
                pass

        formatted.append({
            "tmdb_id": m["id"],
            "title": m["title"],
            "year": release_year,
            "genres": [id_to_name.get(gid, str(gid)) for gid in m.get("genre_ids", [])],
            "overview": m.get("overview", ""),
            "vote_average": m.get("vote_average"),
            "poster_path": m.get("poster_path"),
        })

    return formatted
