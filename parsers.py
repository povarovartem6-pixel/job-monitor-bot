import logging
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from typing import Any

logger = logging.getLogger(__name__)

class BaseParser: ...
class RSSParser(BaseParser): ...
class HTMLParser(BaseParser): ...

def build_default_parsers() -> list[BaseParser]:
    """Возвращает список парсеров по умолчанию. Отредактируйте под себя."""
    return [...]
