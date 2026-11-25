import re
from typing import Optional, Tuple
import logging
from config import STOP_WORDS, MIN_BUDGET

logger = logging.getLogger(__name__)

def extract_budget(text: str) -> Optional[int]: ...
def matches_filters(job: dict, keywords: list[str]) -> Tuple[bool, Optional[str]]: ...
