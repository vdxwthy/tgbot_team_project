import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import common, movie, ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не найден в конфигурации!")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(common.router)
    dp.include_router(movie.router)
    dp.include_router(ai.router)

    logging.info("Бот запущен и ожидает сообщений...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
