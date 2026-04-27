import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOOKING_URL = "https://policlinica24.ru/telegram-booking"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message()
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Записаться к врачу",
                url=BOOKING_URL
            )
        ]
    ])

    await message.answer(
        "Здравствуйте! Нажмите кнопку ниже, чтобы записаться к врачу.",
        reply_markup=kb
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
