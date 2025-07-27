import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

FAST_API_BASE_URL: Final[str] = os.environ.get(
    'FAST_API_BASE_URL', 'http://localhost:8000/')
