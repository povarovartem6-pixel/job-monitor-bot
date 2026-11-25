"""
Фильтрация заказов: извлечение бюджета, проверка стоп-слов и ключевых слов.
"""
import logging
import re
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)


def extract_budget(text: str) -> Optional[int]:
    """Пытается извлечь числовой бюджет (₽) из строки. Возвращает None, если не нашёл."""
    if not text:
        return None
    # Разделители тысяч, неразрывные пробелы
    normalized = text.replace("\xa0", " ").replace("\u2009", " ")
    matches = re.findall(r"\d[\d\s]*\d|\d+", normalized)
    for m in matches:
        try:
            val = int(m.replace(" ", ""))
        except ValueError:
            continue
        # Мелкие числа игнорируем — это скорее сроки, а не бюджеты
        if val >= 1000:
            return val
    return None


def matches_filters(
    job: dict[str, Any], keywords: list[str]
) -> tuple[bool, Optional[str]]:
    """
    Проверяет заказ. Возвращает (подходит_ли, совпавшее_ключевое_слово).
    Побочный эффект: записывает в job["budget_value"] найденный числовой бюджет (или None).
    """
    text = f"{job['title']} {job['description']}".lower()

    # 1. Стоп-слова
    for stop in config.STOP_WORDS:
        if stop in text:
            logger.debug("Заказ %s отклонён стоп-словом '%s'.", job["job_id"], stop)
            return False, None

    # 2. Ключевые слова
    matched_kw: Optional[str] = None
    for kw in keywords:
        if kw.lower() in text:
            matched_kw = kw
            break
    if not matched_kw:
        return False, None

    # 3. Бюджет
    budget_val = (
        extract_budget(job.get("budget_raw", ""))
        or extract_budget(job.get("description", ""))
    )
    job["budget_value"] = budget_val  # сохраняем для форматтера

    if budget_val is not None and budget_val < config.MIN_BUDGET:
        logger.debug(
            "Заказ %s отклонён: бюджет %d < MIN_BUDGET %d.",
            job["job_id"], budget_val, config.MIN_BUDGET,
        )
        return False, None

    return True, matched_kw
