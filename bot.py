import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOOKING_URL = "https://policlinica24.ru/telegram-booking"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    text = message.web_app_data.data
    await message.answer(text)


@dp.message()
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Записаться к врачу",
                    web_app=WebAppInfo(url=BOOKING_URL)
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Здравствуйте! Нажмите кнопку ниже, чтобы записаться к врачу.",
        reply_markup=kb
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
