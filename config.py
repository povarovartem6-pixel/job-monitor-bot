"""
Конфигурация бота. Все значения читаются из .env (или переменных окружения).
Скопируйте .env.example в .env и заполните своими данными.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Переменная окружения {name} не задана. Проверьте .env")
    return value


# --- Секреты (обязательные) ---
BOT_TOKEN: str = _require("BOT_TOKEN")
TARGET_CHAT_ID: int = int(_require("TARGET_CHAT_ID"))
ADMIN_ID: int = int(_require("ADMIN_ID"))

# --- Параметры работы (со значениями по умолчанию) ---
CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "180"))
SILENT_FIRST_RUN: bool = os.getenv("SILENT_FIRST_RUN", "true").lower() in ("1", "true", "yes")
MIN_BUDGET: int = int(os.getenv("MIN_BUDGET", "15000"))
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "jobs.db"))

# --- Ключевые слова (стартовый набор; далее управляются через /add_kw, /del_kw) ---
DEFAULT_KEYWORDS: list[str] = [
    "бот", "воронка", "упаковка", "лендинг", "автоматизация",
    "ии", "нейросет", "telegram", "чат-бот", "парсер", "инфографика",
]

# --- Стоп-слова: если встречаются в тексте заказа, он отбрасывается ---
STOP_WORDS: list[str] = [
    "бесплатно", "за отзыв", "тестовое без оплаты", "стажер", "стажёр",
]
