
import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ==== ВСТАВЬ СВОИ ДАННЫЕ ====
TELEGRAM_TOKEN = "YOUR_TG_TOKEN"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
# ============================
# ============================

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

BASE_URL = "https://api.hh.ru"


# Поиск вакансий
async def search_vacancies(query="python", area=1):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/vacancies",
            params={"text": query, "area": area, "per_page": 5},
            headers=headers,
        )
        r.raise_for_status()
        return r.json().get("items", [])


# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Напиши /search python — и я найду вакансии на hh.ru")


# Команда /search
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    parts = message.text.split(maxsplit=1)
    query = parts[1] if len(parts) > 1 else "python"

    try:
        vacancies = await search_vacancies(query)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
        return

    if not vacancies:
        await message.reply("Ничего не найдено")
    else:
        text = "\n".join(
            [
                f"{v['name']} — {v['employer']['name']} — {v['alternate_url']}"
                for v in vacancies
            ]
        )
        await message.reply(text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
