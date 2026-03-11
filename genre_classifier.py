from sentence_transformers import SentenceTransformer, util
import torch
import os
from dotenv import load_dotenv

load_dotenv()

hf_token = os.getenv("HF_TOKEN")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', use_auth_token=hf_token)

VIBE_LABELS = {
    "Смешной и позитивный 🤡": "комедия юмор смех веселье шутки находчивый позитив",
    "Напряженный и захватывающий 💥": "экшен погоня опасность битва адреналин триллер",
    "Грустный и глубокий 😢": "драма трагедия печаль слезы потеря переживания",
    "Пугающий и мрачный 💀": "ужас страх монстры кошмар темнота мистика",
    "Загадочный и умный 🧠": "детектив тайна расследование загадка интрига ум",
    "Спокойный и добрый 😊": "семейный мультфильм доброта уют дружба"
}

def predict_movie_vibe(text):
    if not text or text == "Описание отсутствует.":
        return "Неизвестный вайб 😶"
        
    try:
        text_embedding = model.encode(text, convert_to_tensor=True)
        
        vibe_names = list(VIBE_LABELS.keys())
        vibe_descriptions = list(VIBE_LABELS.values())
        vibe_embeddings = model.encode(vibe_descriptions, convert_to_tensor=True)
        
        cosine_scores = util.cos_sim(text_embedding, vibe_embeddings)[0]
        
        best_vibe_idx = torch.argmax(cosine_scores).item()
        
        return vibe_names[best_vibe_idx]
        
    except Exception as e:
        print(f"Ошибка при анализе вайба: {e}")
        return "Не удалось определить вайб 🧐"

def predict_genre(text):
    return predict_movie_vibe(text)
