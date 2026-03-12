from aiogram import Router, types, F, html
from aiogram.filters import Command
from handlers.keyboards import get_main_menu
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_name = html.quote(message.from_user.full_name)
    welcome_text = (
        f"👋 <b>Привет, {user_name}!</b>\n\n"
        f"🎬 Я — твой интеллектуальный <b>Кино-Менеджер</b>.\n\n"
        f"<blockquote>Я помогу тебе найти информацию о фильмах и сериалах, "
        f"сделаю краткий пересказ сюжета с помощью ИИ и "
        f"определю жанр по твоему описанию.</blockquote>\n\n"
        f"Воспользуйся кнопками ниже для навигации! 👇"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.message(Command("stop"))
@router.message(F.text == "🛑 Остановить бота")
async def cmd_stop(message: types.Message, state: FSMContext):
    await state.clear()
    stop_text = (
        "👋 <b>До встречи!</b>\n\n"
        "Бот завершил работу. Надеюсь, я помог тебе найти что-то интересное для просмотра! 🍿\n\n"
        "<i>Если захочешь вернуться, просто нажми /start</i>"
    )
    await message.answer(stop_text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())

@router.message(Command("help"))
@router.message(F.text == "📚 Справка")
async def cmd_help(message: types.Message):
    help_text = (
        "📚 <b>Инструкция по использованию:</b>\n\n"
        "🔍 <b>Поиск фильма/сериала</b> — введите название, чтобы получить информацию. Жанр определяется автоматически нашей нейросетью!\n\n"
        "📝 <b>Пересказ сюжета</b> — я найду проект и сделаю краткую выжимку сюжета через ИИ.\n\n"
        "🛑 <b>Остановить бота</b> — завершить текущую сессию.\n\n"
        "<i>Вы можете использовать кнопки меню или команды: /search, /summary, /stop.</i>"
    )
    await message.answer(help_text, parse_mode="HTML")
