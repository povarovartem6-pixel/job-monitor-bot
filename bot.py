"""
Точка входа. Здесь: логирование, мониторинг, хендлеры команд, запуск.
Все команды управления доступны ТОЛЬКО пользователю с ID == config.ADMIN_ID.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import BaseFilter, Command, CommandObject, CommandStart
from aiogram.types import Message

import config
import database as db
from formatter import format_message
from job_filters import matches_filters
from parsers import build_default_parsers

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("job_bot")


# --- Фильтр доступа: только админ ---
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id == config.ADMIN_ID
        )


dp = Dispatcher()


# ============================================================
# ЦИКЛ МОНИТОРИНГА
# ============================================================
async def monitor_loop(bot: Bot) -> None:
    parsers = build_default_parsers()
    first_run_done = not config.SILENT_FIRST_RUN

    if config.SILENT_FIRST_RUN:
        logger.info("SILENT_FIRST_RUN=True: первый цикл только запомнит заказы.")

    async with aiohttp_session() as session:
        while True:
            try:
                keywords = await db.load_keywords()
                if not keywords:
                    logger.warning("Список ключевых слов пуст — заказы не находятся.")
                    await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)
                    continue

                total_new = 0
                any_jobs_seen = False

                for parser in parsers:
                    try:
                        jobs = await parser.fetch(session)
                    except Exception as e:
                        logger.exception(
                            "Критическая ошибка парсера %s: %s",
                            parser.source_name, e,
                        )
                        continue

                    for job in jobs:
                        any_jobs_seen = True
                        if await db.is_job_seen(job["job_id"]):
                            continue

                        ok, matched_kw = matches_filters(job, keywords)
                        # Помечаем в БД до отправки — защита от дублей при сбое
                        await db.mark_job_seen(job["job_id"], job["source"])

                        if not ok or not first_run_done:
                            continue

                        try:
                            await bot.send_message(
                                chat_id=config.TARGET_CHAT_ID,
                                text=format_message(job, matched_kw),
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True,
                            )
                            total_new += 1
                            logger.info("Отправлен заказ: %s", job["title"][:60])
                            await asyncio.sleep(1.5)  # антифлуд
                        except Exception as e:
                            logger.error("Ошибка отправки сообщения: %s", e)

                if not first_run_done:
                    if any_jobs_seen:
                        first_run_done = True
                        logger.info(
                            "Первый запуск завершён: заказы запомнены. "
                            "Рассылка начнётся со следующего цикла."
                        )
                    else:
                        logger.warning(
                            "Первый запуск: парсеры вернули 0 заказов "
                            "(возможно, источники недоступны). Повторю в след. цикле."
                        )
                else:
                    logger.info("Цикл завершён. Новых отправлено: %d", total_new)

            except Exception as e:
                logger.exception("Неожиданная ошибка в цикле мониторинга: %s", e)

            await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)


class aiohttp_session:
    """Контекстный менеджер для aiohttp.ClientSession (чтобы не тащить лишние импорты)."""
    def __init__(self) -> None:
        import aiohttp
        self._aiohttp = aiohttp
        self._session = None

    async def __aenter__(self):
        self._session = self._aiohttp.ClientSession()
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.close()


# ============================================================
# ХЕНДЛЕРЫ КОМАНД (доступны только ADMIN_ID)
# ============================================================
@dp.message(IsAdmin(), CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "🤖 <b>Бот мониторинга заказов запущен!</b>\n\n"
        "Доступные команды:\n"
        "/status — статус мониторинга\n"
        "/add_kw &lt;слово&gt; — добавить ключевое слово\n"
        "/del_kw &lt;слово&gt; — удалить ключевое слово",
        parse_mode=ParseMode.HTML,
    )


@dp.message(IsAdmin(), Command("status"))
async def cmd_status(message: Message) -> None:
    count = await db.count_seen_jobs()
    kws = await db.load_keywords()
    kw_str = ", ".join(kws) if kws else "—"
    await message.answer(
        f"📊 <b>Статус мониторинга</b>\n\n"
        f"🔄 Мониторинг: <b>активен</b>\n"
        f"📦 Заказов в базе: <b>{count}</b>\n"
        f"🔑 Ключевые слова: <i>{html.quote(kw_str)}</i>",
        parse_mode=ParseMode.HTML,
    )


@dp.message(IsAdmin(), Command("add_kw"))
async def cmd_add_kw(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("❌ Укажите слово: /add_kw <слово>")
        return
    word = command.args.strip().lower()
    await db.save_keyword(word)
    await message.answer(f"✅ Ключевое слово «{html.quote(word)}» добавлено.")


@dp.message(IsAdmin(), Command("del_kw"))
async def cmd_del_kw(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("❌ Укажите слово: /del_kw <слово>")
        return
    word = command.args.strip().lower()
    await db.delete_keyword(word)
    await message.answer(f"🗑 Ключевое слово «{html.quote(word)}» удалено.")


# Fallback: ловит команды от посторонних, чтобы писать в лог, но НЕ отвечать
@dp.message(lambda m: m.text and m.text.startswith("/"))
async def cmd_from_stranger(message: Message) -> None:
    if message.from_user and message.from_user.id != config.ADMIN_ID:
        logger.warning(
            "Попытка команды от постороннего: id=%s username=@%s text=%r",
            message.from_user.id, message.from_user.username, message.text,
        )
    # Намеренно молчим


# ============================================================
# ЗАПУСК
# ============================================================
async def main() -> None:
    await db.init_db()
    await db.seed_keywords_if_empty(config.DEFAULT_KEYWORDS)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    monitor_task = asyncio.create_task(monitor_loop(bot))

    try:
        logger.info("Бот запущен. Ожидание команд...")
        await dp.start_polling(bot)
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
