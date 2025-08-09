"""Configure settings for the FastAPI application."""
import os

from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parents[3]
APIS_DIR: Final[Path] = BASE_DIR / 'app' / 'apis'


SYMPTOM_WEIGHTS_FILE: Final[Path] = BASE_DIR / Path(
    os.environ.get('SYMPTOM_WEIGHTS_FILE'))

BIOMARKER_STATS_FILE: Final[Path] = BASE_DIR / Path(
    os.environ.get('BIOMARKER_STATS_FILE'))

FAST_API_HOST: Final[str] = os.environ.get('FAST_API_HOST', '0.0.0.0')

FAST_API_PORT: Final[int] = int(os.environ.get('FAST_API_PORT', 8000))

RENDER_EXTERNAL_HOST: Final[str] = os.environ.get(
    'RENDER_EXTERNAL_HOST', 'https://febrilogic.onrender.com')

STREAMLIT_BASE_URL: Final[str] = os.environ.get(
    'STREAMLIT_BASE_URL', 'http://localhost:8501')

ALGORITHM: Final[str] = os.environ.get('ALGORITHM', 'HS256')

SECRET_KEY: Final[str] = os.environ.get('SECRET_KEY')

ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = int(
    os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

POSTGRES_DATABASE_URL: Final[str] = os.environ.get('POSTGRES_DATABASE_URL')

RESEND_API_KEY: Final[str] = os.environ.get('RESEND_API_KEY')

VERIFICATION_EMAIL_TEMPLATE: Final[Path] = APIS_DIR / Path(
    os.environ.get('VERIFICATION_EMAIL_TEMPLATE'))

RESEND_MAX_RETRIES: Final[int] = int(
    os.environ.get('RESEND_MAX_RETRIES', 3))

GROQ_API_KEY: Final[str] = os.environ.get(
    'GROQ_API_KEY')

GROQ_MODEL: Final[str] = os.environ.get(
    'GROQ_MODEL', 'llama-3.1-8b-instant')

GROQ_URL: Final[str] = os.environ.get(
    'GROQ_URL', 'https://api.groq.com/openai/v1/chat/completions')

GROQ_CONNECT_TIMEOUT: Final[int] = int(
    os.environ.get('GROQ_CONNECT_TIMEOUT', 10))

GROQ_READ_TIMEOUT: Final[int] = int(
    os.environ.get('GROQ_READ_TIMEOUT', 30))

OPENROUTER_API_KEY: Final[str] = os.environ.get(
    'OPENROUTER_API_KEY')

OPENROUTER_MODEL: Final[str] = os.environ.get(
    'OPENROUTER_MODEL', 'openrouter/horizon-beta')

OPENROUTER_URL: Final[str] = os.environ.get(
    'OPENROUTER_URL')

OPENROUTER_CONNECT_TIMEOUT: Final[int] = int(
    os.environ.get('OPENROUTER_CONNECT_TIMEOUT', 10))

OPENROUTER_READ_TIMEOUT: Final[int] = int(
    os.environ.get('OPENROUTER_READ_TIMEOUT', 30))

PROMPT_TEMPLATE_PATH: Final[Path] = BASE_DIR / \
    Path(os.environ.get('PROMPT_TEMPLATE_PATH'))
