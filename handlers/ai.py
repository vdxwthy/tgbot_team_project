from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.movie_api import search_movie
from services.ai_service import summarize_movie_plot, translate_to_english, translate_to_russian
from handlers.states import MovieStates

router = Router()

@router.message(Command("summary"))
@router.message(F.text == "📝 Пересказ сюжета")
async def cmd_summary_start(message: types.Message, state: FSMContext):
    if message.text == "📝 Пересказ сюжета":
        await message.answer("Введите название фильма для краткого пересказа:")
        await state.set_state(MovieStates.waiting_for_movie_summary)
        return

    query = message.text.replace("/summary", "").strip()
    if query:
        return await perform_summary(message, query)
    
    await message.answer("Введите название фильма для краткого пересказа:")
    await state.set_state(MovieStates.waiting_for_movie_summary)

@router.message(MovieStates.waiting_for_movie_summary)
async def process_movie_summary(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if query == "🛑 Остановить бота" or query == "/stop":
        await state.clear()
        from handlers.common import cmd_stop
        return await cmd_stop(message, state)
    
    await state.clear()
    await perform_summary(message, query)

async def perform_summary(message: types.Message, query: str):
    status_msg = await message.answer("🔍 Ищу информацию...")
    
    english_query = await translate_to_english(query)
    movie, error = await search_movie(english_query)

    if error:
        await status_msg.delete()
        return await message.answer(f"❌ {error}")

    plot_text = movie.get('overview')
    if not plot_text or plot_text == "N/A":
        await status_msg.delete()
        return await message.answer(f"К сожалению, для фильма '{movie.get('title')}' нет подробного описания сюжета.")

    await status_msg.edit_text("⏳ Генерирую пересказ...")
    
    summary = await summarize_movie_plot(plot_text)
    
    rus_title = await translate_to_russian(movie.get('title'))
    
    await status_msg.edit_text(
        f"🎬 <b>{rus_title}</b>\n\n"
        f"📝 <b>Краткий пересказ сюжета:</b>\n"
        f"<blockquote>{summary}</blockquote>",
        parse_mode="HTML"
    )
