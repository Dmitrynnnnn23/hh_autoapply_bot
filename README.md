# HH AutoApply Bot 🤖

[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/BotFather)
[![HH.ru](https://img.shields.io/badge/HH.ru-API-red)](https://dev.hh.ru/)
[![Yandex Cloud](https://img.shields.io/badge/Yandex-Cloud-orange)](https://cloud.yandex.ru/)

✨ Умный Telegram-бот для автоматизации поиска работы. Автоматически откликается на вакансии и генерирует персонализированные сопроводительные письма с помощью нейросети Yandex GPT.

## 🌟 Возможности

- 🔍 **Умный поиск вакансий** на hh.ru по заданным критериям
- ⚡ **Автоотклики** на подходящие вакансии
- 🤖 **Генерация сопроводительных писем** с помощью Yandex GPT
- 💰 **Бесплатное использование** в пределах гранта Yandex.Cloud
- 👤 **Простой интерфейс** прямо в Telegram

## 🚀 Быстрый старт

### 📋 Предварительные требования

1. **Yandex.Cloud**
   - 📧 Зарегистрируйтесь на [Yandex.Cloud](https://cloud.yandex.ru/)
   - 💳 Активируйте грант 4000₽ в [разделе Биллинг](https://center.yandex.cloud/billing/accounts/)

2. **HH.ru API**
   - 👨‍💼 Зарегистрируйтесь на [dev.hh.ru](https://dev.hh.ru/)
   - 📱 Создайте приложение в [разделе "Мои приложения"](https://dev.hh.ru/admin)

### 🔑 Настройка приложения HH.ru

При создании приложения укажите:

| Поле | Значение |
|------|----------|
| **Название** | `TelegramBotAutoApply` |
| **Callback URL** | `http://localhost:8000/callback` |
| **Права доступа** | ✅ Доступ к резюме<br>✅ Доступ к откликам |

### 🔐 Получение токенов авторизации

#### Шаг 1: Получение authorization_code

Откройте в браузере ссылку:
```
https://hh.ru/oauth/authorize?response_type=code&client_id=ВАШ_CLIENT_ID&redirect_uri=http://localhost:8000/callback
```

#### Шаг 2: Обмен code на токены

```bash
curl -X POST https://hh.ru/oauth/token \
     -d "grant_type=authorization_code" \
     -d "client_id=ВАШ_CLIENT_ID" \
     -d "client_secret=ВАШ_CLIENT_SECRET" \
     -d "code=ПОЛУЧЕННЫЙ_CODE" \
     -d "redirect_uri=http://localhost:8000/callback"
```

**Ответ:**
```json
{
  "access_token": "xxxx",
  "refresh_token": "yyyy", 
  "token_type": "bearer",
  "expires_in": 1209600
}
```

## ⚙️ Установка и настройка

### 1. Клонирование репозитория

```bash
git clone https://github.com/ваш-username/hh_autoapply_bot.git
cd hh_autoapply_bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` и заполните его:

```env
# Yandex.Cloud
FOLDER_ID=your_folder_id
YANDEX_OAUTH_TOKEN=your_oauth_token
YANDEX_API_KEY=your_api_key

# HH.ru
HH_CLIENT_ID=your_client_id
HH_CLIENT_SECRET=your_client_secret
HH_ACCESS_TOKEN=your_access_token

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 4. Получение ключей доступа

#### 🔧 Yandex.Cloud настройка

**FOLDER_ID:**
- Перейдите в [консоль Yandex.Cloud](https://console.yandex.cloud/folders/)
- Скопируйте идентификатор папки

**OAuth-токен:**
- Получите в [разделе OAuth-токены](https://yandex.cloud/ru/docs/iam/concepts/authorization/oauth-token)
- Действует 1 год

**API-ключ** (действует ~12 часов):
```bash
curl --request POST \
     --data '{"yandexPassportOauthToken":"YOUR_OAUTH_TOKEN"}' \
     https://iam.api.cloud.yandex.net/iam/v1/tokens
```

#### 🤖 Telegram Bot Token
- Напишите [@BotFather](https://t.me/BotFather)
- Создайте нового бота командой `/newbot`
- Скопируйте полученный токен

## 🎯 Использование

1. **Запустите бота:**
```bash
python bot.py
```

2. **Найдите бота в Telegram** по имени

3. **Начните диалог** командой `/start`

4. **Настройте параметры поиска:**
   - Ключевые слова
   - Регион поиска
   - Зарплатные ожидания

5. **Бот автоматически** будет находить вакансии и отправлять отклики!

## 🏗️ Структура проекта

```
hh_autoapply_bot/
├── bot.py                 # Основной файл бота
├── hh_api.py             # Модуль работы с HH.ru API
├── yandex_gpt.py         # Модуль работы с Yandex GPT
├── requirements.txt      # Зависимости Python
├── .env.example         # Пример файла конфигурации
└── README.md            # Документация
```

## 🔧 Технические детали

- **Язык программирования:** Python 3.8+
- **Основные библиотеки:** 
  - `python-telegram-bot` - работа с Telegram API
  - `requests` - HTTP-запросы
  - `python-dotenv` - управление переменными окружения

## 🤝 Разработка

Для внесения изменений:

1. Форкните репозиторий
2. Создайте ветку для новой функциональности
3. Внесите изменения
4. Отправьте pull request

## ⚠️ Важные замечания

- Используйте бота в соответствии с [правилами HH.ru](https://dev.hh.ru/)
- Соблюдайте лимиты API
- Не злоупотребляйте автоматическими откликами

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 📞 Поддержка

Если у вас возникли вопросы:
- Создайте issue в репозитории
- Напишите в Telegram: [@your_username]

---

**⭐ Если проект вам понравился, не забудьте поставить звезду!**

*Сделано с ❤️ для упрощения поиска работы*
