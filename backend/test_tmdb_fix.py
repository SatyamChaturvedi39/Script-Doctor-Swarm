import asyncio, os
from dotenv import load_dotenv
load_dotenv('../.env')
from services.tmdb_client import find_comparable_films, _GENRE_ALIASES

async def test():
    print("sci-fi alias:", _GENRE_ALIASES.get("sci-fi"))
    films = await find_comparable_films(
        genres=["Sci-Fi", "Action"],
        keywords=["space", "alien"],
        max_results=3
    )
    print(f"{len(films)} films found")
    for f in films:
        print(f"  - {f['title']} ({f['year']})")

asyncio.run(test())
