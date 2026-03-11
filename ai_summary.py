import os
import aiohttp
import logging
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def get_movie_summary(title, overview):
    if not OPENROUTER_API_KEY:
        return "Ошибка: API ключ OpenRouter не найден."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        f"Напиши подробный, но емкий пересказ сюжета фильма '{title}' на основе описания: '{overview}'. "
        "Правила оформления:\n"
        "1. Важные имена или ключевые моменты выдели двойными звездочками (например: **Имя Персонажа**).\n"
        "2. Напиши на русском языке, сделай текст увлекательным.\n"
        "3. НЕ ИСПОЛЬЗУЙ никакие HTML теги (<b>, <i> и т.д.), только звездочки для жирного текста.\n"
        "4. Не оборачивай текст в блок цитаты, я сделаю это сам."
    )
    
    payload = {
        "model": "stepfun/step-3.5-flash:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    logger.info(f"--- AI Request Debug ---")
    logger.info(f"Target Movie: {title}")
    logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
                logger.info(f"AI Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"AI Response Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        content = content.replace("```html", "").replace("```", "").strip()
                        return content
                else:
                    error_data = await response.text()
                    logger.error(f"AI Error Response: {error_data}")
                    return f"Ошибка при получении пересказа: {response.status}. {error_data}"
        except Exception as e:
            logger.error(f"AI Request Exception: {e}")
            return f"Исключение при запросе к ИИ: {e}"
    
async def get_recommendations(user_query):
    if not OPENROUTER_API_KEY:
        return []
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        f"Пользователь хочет найти фильмы под такой запрос: '{user_query}'. "
        "Предложи 10 подходящих фильмов или сериалов. "
        "Верни ТОЛЬКО список названий через запятую, без нумерации и лишнего текста. "
        "Пример: Матрица, Начало, Интерстеллар"
    )
    
    payload = {
        "model": "openrouter/hunter-alpha",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        titles = [t.strip() for t in content.split(",") if t.strip()]
                        return titles[:10]
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
    
    return []
