import httpx
from config import OMDB_API_KEY
import asyncio

BASE_URL = "http://www.omdbapi.com/"

async def search_movie(query: str, retries=3):
    if not OMDB_API_KEY:
        return None, "Ошибка: Ключ OMDB_API_KEY не настроен."

    params = {
        "apikey": OMDB_API_KEY,
        "s": query,
    }
    
    async with httpx.AsyncClient() as client:
        for i in range(retries):
            try:
                print(f"DEBUG: Requesting OMDb with params: {params}")
                response = await client.get(BASE_URL, params=params, timeout=10.0)
                print(f"DEBUG: OMDb response status: {response.status_code}")
                
                if response.status_code in [502, 503, 504]:
                    if i < retries - 1:
                        await asyncio.sleep(1)
                        continue
                    return None, "Сервер базы фильмов временно перегружен. Пожалуйста, попробуйте через минуту."

                response.raise_for_status()
                data = response.json()
                print(f"DEBUG: OMDb data: {data}")
                
                if data.get('Response') == 'True' and data.get('Search'):
                    movie_summary = data['Search'][0]
                    imdb_id = movie_summary.get('imdbID')
                    
                    detail_params = {
                        "apikey": OMDB_API_KEY,
                        "i": imdb_id,
                        "plot": "full"
                    }
                    print(f"DEBUG: Requesting details for IMDb ID: {imdb_id}")
                    detail_response = await client.get(BASE_URL, params=detail_params, timeout=10.0)
                    detail_data = detail_response.json()
                    print(f"DEBUG: OMDb detail data: {detail_data}")

                    if detail_data.get('Response') == 'True':
                        movie = {
                            'title': detail_data.get('Title'),
                            'overview': detail_data.get('Plot'),
                            'release_date': detail_data.get('Released'),
                            'vote_average': detail_data.get('imdbRating'),
                            'poster': detail_data.get('Poster')
                        }
                        return movie, None
                
                return None, f"К сожалению, фильм '{query}' не найден. Попробуйте уточнить название."
                
            except httpx.TimeoutException:
                if i < retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None, "Превышено время ожидания ответа от сервера. Попробуйте позже."
            except Exception as e:
                print(f"DEBUG: Search error for '{query}' (attempt {i+1}): {str(e)}")
                if i < retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None, "Произошла ошибка при поиске фильма. Пожалуйста, попробуйте позже."
