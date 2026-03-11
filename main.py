import asyncio
import logging
import os
import html
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from dotenv import load_dotenv

import movie_api
import ai_summary
import genre_classifier
import recommender

load_dotenv()

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

movie_data_cache = {}
recommendations_cache = {}

@dp.message(Command("start"))
async def send_welcome(message: Message):
    welcome_text = (
        "👋 <b>Добро пожаловать в мир кино!</b>\n\n"
        "Я твой умный AI-ассистент, который поможет найти идеальный фильм на вечер. 🤖🍿\n\n"
        "<b>Что я умею:</b>\n"
        "🔍 <b>Поиск:</b> Просто напиши название фильма.\n"
        "🌟 <b>Рекомендации:</b> Команда /ww для подбора по настроению.\n"
        "🧠 <b>AI-пересказ:</b> Генерирую краткую суть сюжета.\n"
        "🎭 <b>Вайб:</b> Анализирую атмосферу картины.\n\n"
        "<i>Нажми на кнопку ниже, чтобы увидеть все команды!</i> 👇"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Команды и помощь 📜", callback_data="show_commands")]
    ])
    
    photo_path = "/Users/evgenijmihajlov/development/machineLearning/course_4/5/welcome_small.jpg"
    
    try:
        photo = FSInputFile(photo_path)
        await message.answer_photo(photo=photo, caption=welcome_text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Failed to send welcome photo: {e}")
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data == "show_commands")
async def handle_show_commands(callback: CallbackQuery):
    commands_text = (
        "📜 <b>Список доступных команд:</b>\n\n"
        "▶️ /start — Перезапустить бота и увидеть приветствие.\n"
        "🎬 <b>[Название фильма]</b> — Просто введи название для поиска информации.\n"
        "🌟 /ww <b>[твой запрос]</b> — Умные рекомендации (например: <i>/ww что-то про космос</i>).\n"
        "🛑 /stop — Вежливое прощание с ботом.\n\n"
        "<i>Просто введи название фильма прямо сейчас и погнали!</i>"
    )
    
    await callback.message.answer(commands_text, parse_mode="HTML")
    await callback.answer()

@dp.message(Command("stop"))
async def send_goodbye(message: Message):
    await message.answer(
        "👋 <b>Был рад помочь!</b>\n\n"
        "Надеюсь, вы нашли отличный фильм на вечер. 🍿\n"
        "Возвращайтесь в любое время — я всегда здесь, чтобы подсказать что-то интересное!\n\n"
        "<i>До скорых встреч!</i> ✨",
        parse_mode="HTML"
    )

@dp.message(Command("ww"))
async def handle_what_to_watch(message: Message):
    user_query = message.text.replace("/ww", "").strip()
    
    if not user_query:
        await message.answer(
            "🎬 <b>Что посмотреть?</b>\n\n"
            "Напиши после команды <code>/ww</code> свой запрос, например:\n"
            "<code>/ww под грустное настроение</code>\n"
            "<code>/ww что-то эпичное про космос</code>",
            parse_mode="HTML"
        )
        return

    status_message = await message.answer(f"🧠 Думаю над рекомендациями по запросу: <i>«{user_query}»</i>...", parse_mode="HTML")
    
    recommendations = await ai_summary.get_recommendations(user_query)
    
    if not recommendations:
        await status_message.edit_text("К сожалению, ИИ не смог подобрать рекомендации. Попробуй другой запрос.")
        return
    
    recommendations_cache[message.from_user.id] = {
        "query": user_query,
        "titles": recommendations
    }
    
    keyboard = build_recommendations_keyboard(recommendations, user_query)
    
    await status_message.edit_text(
        f"🌟 <b>Мои рекомендации для тебя:</b>\n<i>Запрос: «{user_query}»</i>\n\n"
        "Нажми на любой фильм, чтобы узнать о нем подробнее!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

def build_recommendations_keyboard(recommendations, user_query):
    buttons = []
    for title in recommendations:
        short_title = title[:25]
        callback_data = f"ww_select|{short_title}"
        buttons.append([InlineKeyboardButton(text=f"🎬 {title}", callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "back_to_recommendations")
async def handle_back_to_recommendations(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in recommendations_cache:
        await callback.answer("Список рекомендаций устарел.", show_alert=True)
        return
        
    data = recommendations_cache[user_id]
    keyboard = build_recommendations_keyboard(data["titles"], data["query"])
    
    await callback.message.delete()
    await callback.message.answer(
        f"🌟 <b>Мои рекомендации для тебя:</b>\n<i>Запрос: «{data['query']}»</i>\n\n"
        "Нажми на любой вариант, чтобы узнать о нем подробнее!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("ww_select|"))
async def handle_ww_selection(callback: CallbackQuery):
    title = callback.data.split("|")[1]
    
    await callback.message.delete()
    
    await handle_movie_search_with_title(callback.message, title, is_recommendation=True)
    await callback.answer()

async def handle_movie_search_with_title(message: Message, movie_name: str, is_recommendation=False):
    status_message = await message.answer(f"🔍 Ищу информацию о фильме: {movie_name}...")
    
    search_results = await movie_api.search_movie(movie_name)
    
    if not search_results:
        await status_message.edit_text("К сожалению, я не смог найти этот фильм.")
        return

    if len(search_results) == 1 or is_recommendation:
        await process_movie_selection(message, search_results[0], status_message, is_recommendation)
    else:
        buttons = []
        for movie in search_results:
            title = movie.get("title", "Неизвестно")
            release_date = movie.get("release_date", "Неизвестно")
            year = release_date[:4] if release_date != "Неизвестно" else "????"
            
            rec_flag = "1" if is_recommendation else "0"
            callback_data = f"select|movie|{movie.get('id')}|{rec_flag}"
            label = f"🎬 {title} ({year})"
            buttons.append([InlineKeyboardButton(text=label, callback_data=callback_data)])
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await status_message.edit_text("Я нашел несколько вариантов. Выберите нужный:", reply_markup=keyboard)

@dp.message(F.text)
async def handle_movie_search(message: Message):
    await handle_movie_search_with_title(message, message.text)

@dp.callback_query(F.data.startswith("select|"))
async def handle_movie_selection_callback(callback: CallbackQuery):
    parts = callback.data.split("|")
    movie_id = parts[2]
    is_recommendation = parts[3] == "1" if len(parts) > 3 else False
    
    await callback.message.edit_text(f"⏳ Загружаю информацию...")
    
    movie_info = await movie_api.get_movie_details(movie_id, "movie")
    
    if movie_info:
        movie_info["media_type"] = "movie"
        await process_movie_selection(callback.message, movie_info, callback.message, is_recommendation)
    else:
        await callback.message.edit_text("Ошибка при загрузке данных.")

@dp.callback_query(F.data.startswith("get_summary|"))
async def handle_get_summary(callback: CallbackQuery):
    _, media_type, movie_id = callback.data.split("|")
    cache_key = f"{media_type}_{movie_id}"
    
    if cache_key not in movie_data_cache:
        await callback.answer("Данные устарели, попробуйте поискать фильм заново.", show_alert=True)
        return
        
    data = movie_data_cache[cache_key]
    
    status_msg = await callback.message.answer("🍿 <b>Усаживаемся поудобнее...</b>\nСмотрим фильм и пишем для вас пересказ. Это займет пару секунд! 🎬", parse_mode="HTML")
    
    ai_quote = await ai_summary.get_movie_summary(data['title'], data['overview'])
    
    await status_msg.delete()
    
    safe_ai_quote = html.escape(ai_quote)
    safe_ai_quote = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_ai_quote)
    safe_ai_quote = safe_ai_quote.strip()
    
    formatted_ai_quote = f"<blockquote expandable>{safe_ai_quote}</blockquote>"
    
    response = (
        f"💡 <b>Пересказ для «{data['title']}»:</b>\n\n"
        f"{formatted_ai_quote}"
    )
    
    try:
        await callback.message.answer(response, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error sending AI summary: {e}")
        clean_ai_quote = ai_quote.replace("**", "")
        await callback.message.answer(f"💡 Пересказ для «{data['title']}»:\n\n{clean_ai_quote}")

async def process_movie_selection(message: Message, movie_info, status_message, is_recommendation=False):
    title = movie_info.get("title", "Неизвестно")
    release_date = movie_info.get("release_date", "Неизвестно")
    year = release_date[:4] if release_date != "Неизвестно" else "????"
    overview = movie_info.get("overview", "Описание отсутствует.")
    movie_id = movie_info.get("id")
    rating = movie_info.get("vote_average", 0)
    
    await status_message.edit_text(f"🎬 Фильм найден: <b>{title}</b>\n✍️ Анализирую вайб и подбираю рекомендации...", parse_mode="HTML")
    
    details = await movie_api.get_movie_details(movie_id, "movie")
    genres = ", ".join([g["name"] for g in details.get("genres", [])]) if details else "Неизвестно"
    
    movie_vibe = genre_classifier.predict_movie_vibe(overview)
    
    similar_movies_list = await recommender.get_similar_movies(movie_id, overview, "movie")
    similar_text = ""
    if similar_movies_list:
        similar_text = f"\n\n🎬 <b>Похожие по духу фильмы:</b>\n"
        for m in similar_movies_list:
            similar_text += f"• {html.escape(m['title'])}\n"
    
    safe_title = html.escape(title)
    safe_genres = html.escape(genres)
    safe_vibe = html.escape(movie_vibe)
    safe_overview = html.escape(overview)
    poster_path = movie_info.get("poster_path")
    
    rating_text = f"{rating:.1f}/10" if rating > 0 else "Нет данных"
    
    def build_unified_response(overview_limit=None):
        ov = safe_overview
        if overview_limit and len(ov) > overview_limit:
            ov = ov[:overview_limit] + "..."
            
        return (
            f"🎬 <b>{safe_title}</b> ({year})\n"
            f"⭐️ <b>Рейтинг:</b> {rating_text}\n\n"
            f"🎭 <b>Жанры:</b> {safe_genres}\n"
            f"✨ <b>Вайб:</b> {safe_vibe}\n\n"
            f"📖 <b>Оригинальное описание:</b>\n<blockquote expandable>{ov}</blockquote>\n"
            f"{similar_text}"
        )

    response = build_unified_response()
    
    if len(response) > 1024:
        response = build_unified_response(overview_limit=500)
        
    if len(response) > 1024:
        response = build_unified_response(overview_limit=200)

    cache_key = f"movie_{movie_id}"
    movie_data_cache[cache_key] = {
        "title": safe_title,
        "overview": safe_overview
    }
    
    buttons = [
        [InlineKeyboardButton(text="Получить пересказ от ИИ 💡", callback_data=f"get_summary|movie|{movie_id}")]
    ]
    
    if is_recommendation:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к рекомендациям", callback_data="back_to_recommendations")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await status_message.delete()
        
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            await message.answer_photo(photo=poster_url, caption=response, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(response, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        logging.error(f"Failed to send response: {e}")
        await message.answer(f"🎬 {safe_title} ({year})\n⭐️ Рейтинг: {rating_text}\n\n{safe_overview[:500]}...", reply_markup=keyboard)

async def main():
    logging.info("--- Бот успешно инициализирован и готов к работе ---")
    logging.info("Бот запущен и ожидает сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
