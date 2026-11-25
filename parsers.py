"""
Парсеры источников заказов. Каждый парсер наследует BaseParser
и реализует метод fetch() -> list[dict].

Формат возвращаемого словаря:
    {
        "job_id":      "уникальный_идентификатор",
        "source":      "Название источника",
        "title":       "Заголовок заказа",
        "description": "Описание",
        "url":         "https://...",
        "budget_raw":  "сырая строка с бюджетом (может быть пустой)",
    }

⚠️ ВАЖНО: URL и CSS-селекторы в парсерах ниже — ПРИМЕРЫ.
Перед запуском замените их на реальные адреса площадок, которые вы мониторите.
"""
import logging
from typing import Any

import aiohttp
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)


class BaseParser:
    """Базовый класс. Наследники должны задать source_name и реализовать fetch()."""
    source_name: str = "Unknown"

    async def fetch(self, session: aiohttp.ClientSession) -> list[dict[str, Any]]:
        raise NotImplementedError


class RSSParser(BaseParser):
    """
    Парсер RSS-ленты. Использует feedparser.

    Пример использования:
        RSSParser("FL.ru RSS", "https://www.fl.ru/rss/all.xml?category=3")
    """

    def __init__(self, name: str, url: str):
        self.source_name = name
        self.url = url

    async def fetch(self, session: aiohttp.ClientSession) -> list[dict[str, Any]]:
        try:
            async with session.get(
                self.url,
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except Exception as e:
            logger.error("[%s] Ошибка загрузки RSS: %s", self.source_name, e)
            return []

        try:
            feed = feedparser.parse(text)
        except Exception as e:
            logger.error("[%s] Ошибка парсинга RSS: %s", self.source_name, e)
            return []

        jobs: list[dict[str, Any]] = []
        for entry in feed.entries:
            raw_id = entry.get("id") or entry.get("link") or entry.get("title")
            if not raw_id:
                continue
            jobs.append({
                "job_id": f"rss_{self.source_name}_{raw_id}",
                "source": self.source_name,
                "title": entry.get("title", "Без названия"),
                "description": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "budget_raw": "",  # бюджет обычно спрятан в описании
            })
        logger.info("[%s] Получено %d записей из RSS.", self.source_name, len(jobs))
        return jobs


class HTMLParser(BaseParser):
    """
    Парсер HTML-страницы со списком заказов. aiohttp + BeautifulSoup.

    selectors — словарь CSS-селекторов:
        item        — селектор карточки заказа (обязательно)
        title       — заголовок внутри карточки
        description — описание
        budget      — блок с бюджетом
        link        — ссылка на заказ

    Пример:
        HTMLParser(
            "Kwork HTML",
            "https://kwork.ru/projects",
            selectors={
                "item": ".wants-card",
                "title": ".wants-card__header-title",
                "description": ".wants-card__description-text",
                "budget": ".wants-card__price",
                "link": "a",
            },
        )
    """

    def __init__(self, name: str, url: str, selectors: dict[str, str]):
        self.source_name = name
        self.url = url
        self.selectors = selectors

    async def fetch(self, session: aiohttp.ClientSession) -> list[dict[str, Any]]:
        try:
            async with session.get(
                self.url,
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                html_text = await resp.text()
        except Exception as e:
            logger.error("[%s] Ошибка загрузки HTML: %s", self.source_name, e)
            return []

        soup = BeautifulSoup(html_text, "html.parser")
        items = soup.select(self.selectors.get("item", ""))
        jobs: list[dict[str, Any]] = []

        for idx, item in enumerate(items):
            try:
                title_el = item.select_one(self.selectors.get("title", ""))
                desc_el = item.select_one(self.selectors.get("description", ""))
                budget_el = item.select_one(self.selectors.get("budget", ""))
                link_el = item.select_one(self.selectors.get("link", "a"))

                url = ""
                if link_el and link_el.has_attr("href"):
                    url = link_el["href"]
                    if url.startswith("/"):
                        url = self.url.rstrip("/") + url

                # Уникальный ID: ссылка (лучше) или fallback по индексу
                job_id = f"html_{self.source_name}_{hash(url) if url else idx}"

                jobs.append({
                    "job_id": job_id,
                    "source": self.source_name,
                    "title": title_el.get_text(strip=True) if title_el else "Без названия",
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "url": url,
                    "budget_raw": budget_el.get_text(strip=True) if budget_el else "",
                })
            except Exception as e:
                logger.warning(
                    "[%s] Ошибка парсинга элемента #%d: %s",
                    self.source_name, idx, e,
                )

        logger.info("[%s] Получено %d записей из HTML.", self.source_name, len(jobs))
        return jobs


def build_default_parsers() -> list[BaseParser]:
    """Список активных парсеров. ➕ Добавляйте сюда свои источники."""
    return [
        # --- Пример RSS (замените URL!) ---
        RSSParser(
            "FL.ru RSS",
            "https://www.fl.ru/rss/all.xml?category=3",
        ),
        # --- Пример HTML (замените URL и селекторы!) ---
        HTMLParser(
            "Kwork HTML",
            "https://kwork.ru/projects",
            selectors={
                "item": ".wants-card",
                "title": ".wants-card__header-title",
                "description": ".wants-card__description-text",
                "budget": ".wants-card__price",
                "link": "a",
            },
        ),
    ]
