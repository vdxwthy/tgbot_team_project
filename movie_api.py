import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

async def search_movie(title):
    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        return []
    
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "ru-RU"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["results"]:
                    valid_results = data["results"]
                    
                    if not valid_results: return []
                    
                    def sort_key(item):
                        item_title = (item.get("title") or "").lower()
                        is_exact = 1 if item_title == title.lower() else 0
                        return (is_exact, item.get("vote_count", 0), item.get("popularity", 0))
                    
                    valid_results.sort(key=sort_key, reverse=True)
                    
                    for r in valid_results:
                        r["media_type"] = "movie"
                    
                    return valid_results[:10]
    return []

async def get_movie_details(item_id, media_type="movie"):
    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        return None
    
    url = f"{TMDB_BASE_URL}/{media_type}/{item_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "ru-RU"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
    return None
