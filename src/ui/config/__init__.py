"""Configuration settings for the Streamlit app."""
import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

FAST_API_BASE_URL: Final[str] = os.environ.get(
    'FAST_API_BASE_URL', 'http://localhost:8000/')

FAST_API_CONNECT_TIMEOUT: Final[int] = int(os.environ.get(
    'FAST_API_CONNECT_TIMEOUT', 5))

FAST_API_READ_TIMEOUT: Final[int] = int(os.environ.get(
    'FAST_API_READ_TIMEOUT', 10))
