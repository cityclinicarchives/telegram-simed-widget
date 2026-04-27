import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN:
    raise RuntimeError("Заполните BOT_TOKEN в .env")
if not WEBAPP_URL:
    raise RuntimeError("Заполните WEBAPP_URL в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("Получил данные из формы, но не смог их прочитать.")
        return

    if data.get("type") == "booking_success":
        doctor = data.get("doctor_name", "выбранному врачу")
        date = data.get("date", "выбранную дату")
        time_interval = data.get("time_interval", "выбранное время")
        await message.answer(
            f"✅ Вы записаны к врачу {doctor} на {date} {time_interval}.\n\n"
            f"Ждем Вас в нашей клинике!"
        )
    else:
        await message.answer("Получил данные из формы: " + json.dumps(data, ensure_ascii=False))


@dp.message()
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Записаться к врачу",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    await message.answer("Здравствуйте! Нажмите кнопку ниже, чтобы записаться к врачу.", reply_markup=kb)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
