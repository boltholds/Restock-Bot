import asyncio
import logging

from aiogram import Bot, Dispatcher

from restock_bot.config import settings
from restock_bot.db import init_db, close_db
from restock_bot.bots.reception.handlers import router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not settings.reception_bot_token:
        raise RuntimeError("RECEPTION_BOT_TOKEN is not set")

    await init_db()

    bot = Bot(token=settings.reception_bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

def run() -> None:
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
