import openai
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

# Настройка асинхронного клиента OpenAI для OpenRouter
client = openai.AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

AI_MODELS = [
    "google/gemini-2.0-flash-001",
    "openrouter/healer-alpha",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "sourceful/riverflow-v2-pro"
]

async def _call_ai_with_fallback(messages, max_tokens=1000, timeout=15):
    last_error = None
    for model_name in AI_MODELS:
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                timeout=timeout,
                extra_headers={
                    "HTTP-Referer": "https://github.com/trae-ai",
                    "X-Title": "Movie Manager Bot"
                }
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"DEBUG: Model {model_name} failed: {str(e)}")
            last_error = e
            continue
    
    raise last_error

async def translate_to_english(text: str):
    if not OPENROUTER_API_KEY:
        return text

    messages = [
        {"role": "system", "content": "You are a professional translator. Translate the movie title from Russian to English. Output ONLY the English title, nothing else."},
        {"role": "user", "content": text}
    ]

    try:
        translated = await _call_ai_with_fallback(messages, max_tokens=30, timeout=10)
        print(f"DEBUG: Translated '{text}' to '{translated}'")
        return translated
    except Exception as e:
        print(f"DEBUG: All models failed for translation to English: {str(e)}")
        return text

async def translate_to_russian(text: str):
    if not OPENROUTER_API_KEY:
        return text

    messages = [
        {"role": "system", "content": "You are a professional translator. Translate the text to Russian. Output ONLY the translated text, nothing else."},
        {"role": "user", "content": text}
    ]

    try:
        return await _call_ai_with_fallback(messages, max_tokens=1000, timeout=15)
    except Exception as e:
        print(f"DEBUG: All models failed for translation to Russian: {str(e)}")
        return text

async def summarize_movie_plot(plot_text: str):
    if not OPENROUTER_API_KEY:
        return "Ошибка: Ключ OpenRouter не настроен."

    messages = [
        {"role": "system", "content": "Ты — помощник киномана. Сделай очень краткий и интересный пересказ сюжета фильма (2-3 предложения) на русском языке на основе предоставленного описания."},
        {"role": "user", "content": f"Сюжет фильма: {plot_text}"}
    ]

    try:
        return await _call_ai_with_fallback(messages, max_tokens=400, timeout=20)
    except Exception as e:
        print(f"DEBUG: All models failed for summarization: {str(e)}")
        return "Не удалось сгенерировать пересказ из-за временной недоступности ИИ-сервисов."
