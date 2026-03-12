from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.movie_api import search_movie
from services.ai_service import translate_to_english, translate_to_russian
from services.transformer_service import classify_genre_local
from handlers.states import MovieStates

router = Router()

@router.message(Command("search"))
@router.message(F.text == "🔍 Поиск фильма/сериала")
async def cmd_search_start(message: types.Message, state: FSMContext):
    if message.text == "🔍 Поиск фильма/сериала":
        await message.answer("Введите название фильма или сериала для поиска:")
        await state.set_state(MovieStates.waiting_for_movie_search)
        return

    query = message.text.replace("/search", "").strip()
    if query:
        return await perform_search(message, query)
    
    await message.answer("Введите название фильма или сериала для поиска:")
    await state.set_state(MovieStates.waiting_for_movie_search)

@router.message(MovieStates.waiting_for_movie_search)
async def process_movie_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if query == "🛑 Остановить бота" or query == "/stop":
        await state.clear()
        from handlers.common import cmd_stop
        return await cmd_stop(message, state)
    
    await state.clear()
    await perform_search(message, query)

async def perform_search(message: types.Message, query: str):
    status_msg = await message.answer("🔍 Ищу информацию...")
    
    english_query = await translate_to_english(query)
    movie, error = await search_movie(english_query)

    if error:
        await status_msg.delete()
        return await message.answer(f"❌ {error}")

    title = movie.get('title')
    overview = movie.get('overview', 'Нет описания.')
    release_date_raw = movie.get('release_date', 'неизвестно')
    rating = movie.get('vote_average', 'неизвестно')
    poster = movie.get('poster')
    
    def format_date_ru(date_str):
        months_map = {
            'Jan': 'янв', 'Feb': 'фев', 'Mar': 'мар', 'Apr': 'апр',
            'May': 'мая', 'Jun': 'июня', 'Jul': 'июля', 'Aug': 'авг',
            'Sep': 'сент', 'Oct': 'окт', 'Nov': 'ноя', 'Dec': 'дек'
        }
        for eng, ru in months_map.items():
            if eng in date_str:
                return date_str.replace(eng, ru)
        return date_str

    release_date = format_date_ru(release_date_raw)
    
    rus_title = await translate_to_russian(title)
    rus_overview = await translate_to_russian(overview)
    
    genre = await classify_genre_local(rus_overview)

    response_text = (
        f"🎬 <b>{rus_title}</b>\n\n"
        f"🎭 <b>Определенный жанр:</b> <code>{genre}</code>\n"
        f"📅 <b>Дата выхода:</b> <code>{release_date}</code>\n"
        f"⭐ <b>Рейтинг IMDb:</b> <code>{rating}/10</code>\n\n"
        f"📖 <b>Описание:</b>\n"
        f"<blockquote expandable>{rus_overview}</blockquote>"
    )
    
    await status_msg.delete()
    if poster and poster != "N/A":
        await message.answer_photo(poster, caption=response_text, parse_mode="HTML")
    else:
        await message.answer(response_text, parse_mode="HTML")
