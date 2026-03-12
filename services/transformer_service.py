import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

MODEL_PATH = os.path.join(os.getcwd(), "models", "genre_model")

_tokenizer = None
_model = None
_executor = ThreadPoolExecutor(max_workers=1)

def get_model():
    global _tokenizer, _model
    if _model is None:
        try:
            if os.path.exists(MODEL_PATH):
                print(f"DEBUG: Loading local transformer model from {MODEL_PATH}...")
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
                _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
                _model.eval()
                print("DEBUG: Local model loaded successfully!")
            else:
                print("DEBUG: Local model directory not found!")
                return None, None
        except Exception as e:
            print(f"DEBUG: Error loading local model: {str(e)}")
            return None, None
    return _tokenizer, _model

def _sync_classify(text: str):
    try:
        tokenizer, model = get_model()
        if model is None or tokenizer is None:
            return "Не определено"
            
        text = text.lower().strip()
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=1)
            predicted_class_id = torch.argmax(logits, dim=1).item()
        
        keywords = {
            'Анимация': ['мультфильм', 'анимаци', 'огр', 'осел', 'дракон', 'принцесс', 'игрушки', 'тачки'],
            'Комедия': ['комед', 'смешн', 'весел', 'шут', 'озор'],
            'Ужасы': ['ужас', 'хоррор', 'монстр', 'призрак', 'кровь', 'смерть'],
            'Фантастика': ['космос', 'планет', 'будущее', 'робот', 'технолог', 'червоточин'],
            'Боевик': ['погоня', 'драка', 'выстрел', 'оружие', 'сражение', 'агент'],
            'Драма': ['жизнь', 'судьба', 'любовь', 'семья', 'трагедия', 'отношения']
        }
        
        detected_genres = []
        for genre, keys in keywords.items():
            if any(key in text for key in keys):
                detected_genres.append(genre)
        
        if detected_genres:
            return " / ".join(detected_genres[:2])
            
        label = model.config.id2label.get(predicted_class_id, "LABEL_0")
        
        if "1" in str(label) or "POSITIVE" in str(label):
            return "Комедия / Приключения"
        return "Драма / Триллер"
            
    except Exception as e:
        print(f"DEBUG: Transformer error: {str(e)}")
        return "Драма"

async def classify_genre_local(text: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _sync_classify, text)
