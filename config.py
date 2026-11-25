import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "180"))
SILENT_FIRST_RUN = os.getenv("SILENT_FIRST_RUN", "true").lower() == "true"
MIN_BUDGET = int(os.getenv("MIN_BUDGET", "15000"))

DB_PATH = os.getenv("DB_PATH", "jobs.db")

KEYWORDS = [...]
STOP_WORDS = [...]

# Validate
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан...")
if TARGET_CHAT_ID == 0:
    raise ValueError("TARGET_CHAT_ID не задан...")
if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID не задан...")
