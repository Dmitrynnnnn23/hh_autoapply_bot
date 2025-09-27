import asyncio
import json
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ==== ВСТАВЬ СВОИ ДАННЫЕ ====
TELEGRAM_TOKEN = "YOUR_TG_TOKEN"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
RESUME_ID = "YOUR_RESUME_ID"
# ============================

BASE_URL = "https://api.hh.ru"
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

APPLIED_FILE = "applied.json"

if os.path.exists(APPLIED_FILE):
    with open(APPLIED_FILE, "r", encoding="utf-8") as f:
        applied_ids = set(json.load(f))
else:
    applied_ids = set()

autoapply_task: asyncio.Task | None = None
stop_event = asyncio.Event()


# === API HH ===
async def search_vacancies(query: str, area: int = 1):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/vacancies",
            params={"text": query, "area": area, "per_page": 5},
            headers=headers,
        )
        r.raise_for_status()
        return r.json().get("items", [])


async def apply_to_vacancy(vacancy_id: str, vacancy_name: str, url: str, chat_id: int):
    if vacancy_id in applied_ids:
        await bot.send_message(chat_id, f"⚠️ Уже откликался ранее: {vacancy_name} — {url}")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    endpoint = f"{BASE_URL}/negotiations"
    params = {"vacancy_id": vacancy_id, "resume_id": RESUME_ID}

    async with httpx.AsyncClient() as client:
        r = await client.post(endpoint, headers=headers, params=params)

    if r.status_code in (201, 202):
        applied_ids.add(vacancy_id)
        with open(APPLIED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(applied_ids), f, ensure_ascii=False, indent=2)

        await bot.send_message(chat_id, f"✅ Отклик отправлен: {vacancy_name} — {url}")
        return True
    else:
        try:
            err = r.json()
            if "errors" in err and err["errors"]:
                code = err["errors"][0].get("value")
                if code == "test_required":
                    msg = "❌ Требуется тест — автоотклик невозможен"
                elif code == "already_applied":
                    msg = "⚠️ Уже откликался ранее"
                elif code == "resume_not_published":
                    msg = "❌ Резюме скрыто или не опубликовано"
                else:
                    msg = f"❌ Ошибка: {code}"
            else:
                msg = f"❌ Ошибка {r.status_code}: {r.text}"
        except Exception:
            msg = f"❌ Ошибка {r.status_code}: {r.text}"

        await bot.send_message(chat_id, f"{msg}\n{vacancy_name} — {url}")
        return False


# === Команды ===
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот автооткликов на hh.ru.\n\n"
        "Команды:\n"
        "/search <запрос> — поиск вакансий\n"
        "/autoapply <запрос> — автоотклики\n"
        "/stop — остановить автоотклики"
    )


@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("❌ Укажи запрос, например: /search python junior")
        return

    query = parts[1]
    try:
        vacancies = await search_vacancies(query)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
        return

    if not vacancies:
        await message.reply("Ничего не найдено")
    else:
        text = "\n".join(
            [f"{v['name']} — {v['employer']['name']} — {v['alternate_url']}" for v in vacancies]
        )
        await message.reply(text)


@dp.message(Command("autoapply"))
async def cmd_autoapply(message: types.Message):
    global autoapply_task, stop_event
    if autoapply_task and not autoapply_task.done():
        await message.reply("Автоотклики уже запущены!")
        return


    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("❌ Укажи запрос, например: /autoapply python junior")
        return

    query = parts[1]
    stop_event.clear()
    autoapply_task = asyncio.create_task(autoapply_loop(message.chat.id, query))
    await message.reply(f"🚀 Автоотклики запущены по запросу: {query}")


@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    global autoapply_task, stop_event
    if autoapply_task and not autoapply_task.done():
        stop_event.set()
        await message.reply("⛔ Автоотклики остановлены.")
    else:
        await message.reply("Автоотклики не были запущены.")


# === Фоновая задача автооткликов ===
async def autoapply_loop(chat_id: int, query: str):
    while not stop_event.is_set():
        try:
            vacancies = await search_vacancies(query)
            if not vacancies:
                await bot.send_message(chat_id, "Новых вакансий не найдено")
            else:
                for v in vacancies:
                    await apply_to_vacancy(v["id"], v["name"], v["alternate_url"], chat_id)
        except Exception as e:
            await bot.send_message(chat_id, f"Ошибка автоотклика: {e}")

        await asyncio.sleep(60)


# === Main ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())