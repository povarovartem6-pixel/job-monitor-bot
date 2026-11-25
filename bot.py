import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import BaseFilter, Command, CommandObject, CommandStart
from aiogram.types import Message

import config
from database import ...
from parsers import build_default_parsers
from job_filters import matches_filters
from formatter import format_message
