"""
Форматирование сообщения для Telegram (HTML-разметка).
"""
from typing import Any

from aiogram import html

import config


def format_message(job: dict[str, Any], matched_kw: str) -> str:
    """Собирает HTML-сообщение о заказе."""
    desc = job.get("description") or "Описание отсутствует."
    if len(desc) > 350:
        desc = desc[:347] + "..."

    budget_val = job.get("budget_value")
    if budget_val is not None:
        if budget_val >= config.MIN_BUDGET:
            budget_str = f"от {budget_val:,} ₽".replace(",", " ")
        else:
            budget_str = f"{budget_val:,} ₽".replace(",", " ")
    else:
        budget_str = "Бюджет не указан"

    return (
        f"🔥 <b>Новый заказ!</b> [{html.quote(job['source'])}]\n\n"
        f"📌 <b>Задача:</b> {html.quote(job['title'])}\n"
        f"💰 <b>Бюджет:</b> {budget_str}\n"
        f"🔑 <b>Совпадение:</b> #{html.quote(matched_kw)}\n\n"
        f"📝 <b>Описание:</b>\n{html.quote(desc)}\n\n"
        f"🔗 <a href=\"{html.quote(job['url'])}\">Открыть заказ</a>"
    )
