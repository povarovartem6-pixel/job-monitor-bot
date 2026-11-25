# 🤖 Job Monitor Bot

Telegram-бот на **aiogram 3.x**, который каждые N минут проверяет RSS-ленты и HTML-страницы с заказами/вакансиями, фильтрует их по ключевым словам и минимальному бюджету, сохраняет просмотренные ID в SQLite (защита от дублей) и присылает новые релевантные заказы в указанный чат.

## ✨ Возможности

- 📡 Поддержка **RSS** (feedparser) и **HTML** (aiohttp + BeautifulSoup4).
- 🔍 Фильтрация по ключевым словам и стоп-словам.
- 💰 Отсев заказов с бюджетом ниже `MIN_BUDGET`. Заказы без указанного бюджета проходят.
- 🗄 **SQLite**-база для защиты от повторных уведомлений.
- 🤫 Флаг `SILENT_FIRST_RUN`: при первом запуске не спамит старыми заказами.
- 🔒 Команды управления доступны **только одному** пользователю (`ADMIN_ID`).
- ⚙️ Живое управление ключевыми словами через `/add_kw` и `/del_kw`.

## 📁 Структура

```
.
├── bot.py              # Точка входа: мониторинг, хендлеры, запуск
├── config.py           # Все настройки (из .env)
├── database.py         # SQLite-операции
├── parsers.py          # RSS + HTML парсеры
├── job_filters.py      # Фильтрация заказов
├── formatter.py        # Формирование HTML-сообщения
├── requirements.txt
├── .env.example
├── .gitignore
├── systemd/
│   └── job-bot.service
└── README.md
```

## 🚀 Установка

```bash
git clone https://github.com/<your_username>/job-monitor-bot.git
cd job-monitor-bot

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Откройте .env и заполните BOT_TOKEN, TARGET_CHAT_ID, ADMIN_ID
```

## 🔑 Получение данных

**`BOT_TOKEN`** — создайте бота у [@BotFather](https://t.me/BotFather), команда `/newbot`.

**`ADMIN_ID`** — напишите [@userinfobot](https://t.me/userinfobot), он вернёт ваш `Id`.

**`TARGET_CHAT_ID`** — куда слать заказы (чат команды или канал):
1. Добавьте бота в чат/канал как администратора.
2. Отправьте туда любое сообщение.
3. Откройте `https://api.telegram.org/bot<ТОКЕН>/getUpdates`.
4. Найдите `"chat":{"id":-100...}` — это и есть `TARGET_CHAT_ID`.

## ⚙️ Настройка источников

Откройте `parsers.py` → функцию `build_default_parsers()` — там два примера.

- **RSS**: замените URL на реальную ленту.
- **HTML**: замените URL и CSS-селекторы под конкретную площадку.

Добавить новый источник просто: создайте новый `RSSParser(...)` или `HTMLParser(...)` и добавьте в список.

## ▶️ Запуск

### Локально
```bash
python bot.py
```

### На VPS (systemd)
```bash
sudo cp systemd/job-bot.service /etc/systemd/system/
# отредактируйте пути и пользователя в файле
sudo systemctl daemon-reload
sudo systemctl enable --now job-bot
sudo systemctl status job-bot
sudo journalctl -u job-bot -f
```

### На VPS (screen)
```bash
screen -S job-bot
python bot.py
# отключиться: Ctrl+A, затем D
# вернуться: screen -r job-bot
```

## 💬 Команды бота

| Команда | Действие |
|---|---|
| `/start` | Приветствие |
| `/status` | Кол-во заказов в базе + активные ключевые слова |
| `/add_kw <слово>` | Добавить ключевое слово |
| `/del_kw <слово>` | Удалить ключевое слово |

Все команды выполняет **только** пользователь с ID `ADMIN_ID`. Посторонние не получают ответа (в лог пишется предупреждение).

## 📌 Пример сообщения в чате

> 🔥 **Новый заказ!** [FL.ru RSS]
>
> 📌 **Задача:** Разработать Telegram-бота для приёма заявок
> 💰 **Бюджет:** от 45 000 ₽
> 🔑 **Совпадение:** #telegram
>
> 📝 **Описание:**
> Нужен чат-бот на aiogram с приёмом заявок и передачей в CRM...
>
> 🔗 [Открыть заказ](https://www.fl.ru/projects/12345678)

## 🛠 Расширение

Чтобы добавить источник — откройте `parsers.py`, добавьте экземпляр `RSSParser` / `HTMLParser` в `build_default_parsers()`. Всё остальное подхватится автоматически.

Чтобы изменить формат сообщения — отредактируйте `formatter.py`.

Чтобы изменить правила фильтрации — `job_filters.py`.

## 📄 Лицензия

MIT. Используйте на здоровье.
