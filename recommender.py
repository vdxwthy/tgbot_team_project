from sentence_transformers import SentenceTransformer, util
import torch
import movie_api

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

async def get_similar_movies(movie_id, query_overview, media_type="movie", top_k=3):
    if not query_overview or query_overview == "Описание отсутствует.":
        return []

    import aiohttp
    import os
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    
    url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}/recommendations"
    params = {"api_key": TMDB_API_KEY, "language": "ru-RU"}
    
    candidate_movies = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                candidate_movies = data.get("results", [])

    if not candidate_movies:
        url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}/similar"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    candidate_movies = data.get("results", [])

    if not candidate_movies:
        return []

    candidate_movies = [m for m in candidate_movies if m.get("overview")]
    if not candidate_movies: return []

    candidate_overviews = [m.get("overview") for m in candidate_movies]
    candidate_titles = [m.get("title") or m.get("name") or "Неизвестно" for m in candidate_movies]
    
    query_embedding = model.encode(query_overview, convert_to_tensor=True)
    candidate_embeddings = model.encode(candidate_overviews, convert_to_tensor=True)
    
    cosine_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
    
    top_results = torch.topk(cosine_scores, k=min(top_k, len(candidate_titles)))
    
    recommendations = []
    for score, idx in zip(top_results[0], top_results[1]):
        recommendations.append({
            "title": candidate_titles[idx],
            "score": float(score)
        })
        
    return recommendations
