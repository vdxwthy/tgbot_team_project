from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    buttons = [
        [KeyboardButton(text="🔍 Поиск фильма/сериала"), KeyboardButton(text="📝 Пересказ сюжета")],
        [KeyboardButton(text="📚 Справка"), KeyboardButton(text="🛑 Остановить бота")]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню..."
    )
    return keyboard
