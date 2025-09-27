import asyncio
import json
import os
import logging
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from yandex_cloud_ml_sdk import YCloudML

# ==== Логирование ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hh_bot")

# ==== Конфигурация ====
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ТГ"
ACCESS_TOKEN = "ВАШ_HH_ACCESS_TOKEN"
RESUME_ID = "ВАШ_RESUME_ID"
YANDEX_API_KEY = "ВАШ_YANDEX_API_KEY"
FOLDER_ID = "ВАШ_FOLDER_ID"
REAL_NAME = "Иванов Иван"


BASE_URL = "https://api.hh.ru"
APPLIED_FILE = "applied.json"

# ==== Telegram ====
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ==== Яндекс GPT ====
try:
    sdk = YCloudML(folder_id=FOLDER_ID, auth=YANDEX_API_KEY)
    model = sdk.models.completions("yandexgpt").configure(temperature=0.4, max_tokens=800)
    yandex_ready = True
except Exception as e:
    logger.warning(f"Yandex GPT не доступен: {e}")
    yandex_ready = False

# ==== Хранилище откликов ====
def load_applied():
    if os.path.exists(APPLIED_FILE):
        try:
            return set(json.load(open(APPLIED_FILE, encoding="utf-8")))
        except Exception as e:
            logger.error(f"Ошибка чтения applied.json: {e}")
    return set()

def save_applied():
    try:
        json.dump(list(applied), open(APPLIED_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения applied.json: {e}")

applied = load_applied()
stop_event = asyncio.Event()
autoapply_task: asyncio.Task | None = None

# ==== HH API ====
async def hh_request(method: str, url: str, **kwargs):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "User-Agent": "HH-Client/1.0"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.request(method, url, headers=headers, **kwargs)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HH API {url} вернул {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        logger.error(f"Ошибка запроса к HH API {url}: {e}")
    return None

async def search_vacancies(query: str, area: int = 1, per_page: int = 10):
    data = await hh_request("GET", f"{BASE_URL}/vacancies", params={"text": query, "area": area, "per_page": per_page})
    return data.get("items", []) if data else []

async def get_vacancy(vacancy_id: str):
    return await hh_request("GET", f"{BASE_URL}/vacancies/{vacancy_id}")

async def get_resume():
    return await hh_request("GET", f"{BASE_URL}/resumes/{RESUME_ID}")

# ==== Сопроводительное письмо ====
def generate_letter(resume, vacancy):
    if not yandex_ready:
        return f"Здравствуйте!\nМеня заинтересовала вакансия {vacancy.get('name')} в {vacancy['employer']['name']}.\n\nС уважением,\n{REAL_NAME}"

    prompt = f"""
Составь профессиональное сопроводительное письмо (150-250 слов).
Кандидат: {REAL_NAME}
Вакансия: {vacancy.get('name')} в {vacancy['employer']['name']}

Инфо кандидата: {resume}
Описание вакансии: {vacancy.get('description', '')[:1000]}

Сопроводительное письмо (без подписи в конце):
"""
    try:
        op = model.run_deferred(prompt)
        result = op.wait()
        text = result.alternatives[0].text.strip()

        # Убираем возможные подписи, которые мог добавить ИИ
        text = text.split('С уважением,')[0].split('С уважением\n')[0].strip()
        text = text.split('С наилучшими пожеланиями,')[0].split('С наилучшими пожеланиями\n')[0].strip()

        # Добавляем нашу подпись только один раз
        text += f"\n\nС уважением,\n{REAL_NAME}"
        return text
    except Exception as e:
        logger.error(f"Ошибка генерации письма: {e}")
        return f"Здравствуйте!\nМеня заинтересовала вакансия {vacancy.get('name')}.\n\nС уважением,\n{REAL_NAME}"

# ==== Отклик ====
async def apply(vacancy_id: str, chat_id: int):
    if vacancy_id in applied:
        return

    vacancy, resume = await get_vacancy(vacancy_id), await get_resume()
    if not vacancy or not resume:
        await bot.send_message(chat_id, f"❌ Не удалось получить данные для вакансии {vacancy_id}")
        return

    letter = generate_letter(resume, vacancy)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{BASE_URL}/negotiations", data={
            "vacancy_id": vacancy_id,
            "resume_id": RESUME_ID,
            "message": letter
        }, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "User-Agent": "HH-Client/1.0"})
    if r.status_code in (201, 202, 204):
        applied.add(vacancy_id); save_applied()
        await bot.send_message(chat_id, f"✅ Отклик отправлен: {vacancy['name']}\n{vacancy['alternate_url']}")
        await bot.send_message(chat_id, f"✉️ Сопроводительное:\n\n{letter}")
    else:
        await bot.send_message(chat_id, f"❌ Ошибка отклика {r.status_code}: {r.text[:200]}")

# ==== Цикл автооткликов ====
async def autoapply_loop(chat_id: int, query: str):
    while not stop_event.is_set():
        vacancies = await search_vacancies(query, per_page=5)
        new_vacancies = [v for v in vacancies if v['id'] not in applied]
        for v in new_vacancies:
            await apply(v['id'], chat_id)
            await asyncio.sleep(15)
        await asyncio.sleep(300)

# ==== Команды ====
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer(f"🤖 Бот запущен. Имя: {REAL_NAME}\n\nКоманды:\n/search <текст>\n/autoapply <текст>\n/stop\n/stats")

@dp.message(Command("search"))
async def cmd_search(msg: types.Message):
    q = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else None
    if not q: return await msg.answer("❌ Укажи запрос: /search Python")
    vacancies = await search_vacancies(q, per_page=5)
    if not vacancies: return await msg.answer("❌ Вакансий нет")
    text = "\n\n".join([f"{v['name']} ({v['employer']['name']})\n{v['alternate_url']}" for v in vacancies])
    await msg.answer(f"📋 Найдено:\n\n{text}")

@dp.message(Command("autoapply"))
async def cmd_auto(msg: types.Message):
    global autoapply_task
    q = msg.text.split(maxsplit=1)[1] if len(msg.text.split()) > 1 else None
    if not q: return await msg.answer("❌ Укажи запрос: /autoapply Python")
    stop_event.clear()
    autoapply_task = asyncio.create_task(autoapply_loop(msg.chat.id, q))
    await msg.answer(f"🚀 Автоотклики по запросу '{q}' запущены!")

@dp.message(Command("stop"))
async def cmd_stop(msg: types.Message):
    global autoapply_task
    stop_event.set()
    if autoapply_task: autoapply_task.cancel()
    await msg.answer("⛔ Автоотклики остановлены.")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    await msg.answer(f"📨 Всего откликов: {len(applied)}")

# ==== Запуск ====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())