"""Configure settings for the FastAPI application."""
import os

from pathlib import Path
from typing import Final

from dotenv import load_dotenv

if os.path.exists(Path(__file__).parent.parent / '.env.local'):
    load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env.local')
else:
    load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[3]
APIS_DIR: Final[Path] = BASE_DIR / 'app' / 'apis'


AWS_ACCESS_KEY_ID: Final[str] = os.environ.get('AWS_ACCESS_KEY_ID')

AWS_SECRET_ACCESS_KEY: Final[str] = os.environ.get('AWS_SECRET_ACCESS_KEY')

BUCKET_NAME: Final[str] = os.environ.get('BUCKET_NAME')

SYMPTOM_WEIGHTS_OBJECT: Final[str] = os.environ.get('SYMPTOM_WEIGHTS_OBJECT')

BIOMARKERS_RANGES_OBJECT: Final[str] = os.environ.get(
    'BIOMARKERS_RANGES_OBJECT')

if not os.path.exists((BASE_DIR / 'data' / 'private')):
    Path.mkdir(BASE_DIR / 'data' / 'private')

BIOMARKERS_RANGES_PATH: Final[Path] = BASE_DIR / \
    'data' / 'private' / BIOMARKERS_RANGES_OBJECT

SYMPTOM_WEIGHTS_PATH: Final[Path] = BASE_DIR / \
    'data' / 'private' / SYMPTOM_WEIGHTS_OBJECT

FAST_API_HOST: Final[str] = os.environ.get('FAST_API_HOST', '0.0.0.0')

FAST_API_PORT: Final[int] = int(os.environ.get('FAST_API_PORT', 8000))

RENDER_EXTERNAL_HOST: Final[str] = os.environ.get(
    'RENDER_EXTERNAL_HOST')

STREAMLIT_BASE_URL: Final[str] = os.environ.get(
    'STREAMLIT_BASE_URL', 'https://www.febrilogic.com')

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

SUPPORT_REQUEST_TEMPLATE: Final[Path] = APIS_DIR / Path(
    os.environ.get('SUPPORT_REQUEST_TEMPLATE'))

PASSWORD_RESET_EMAIL_TEMPLATE: Final[Path] = APIS_DIR / Path(
    os.environ.get('PASSWORD_RESET_EMAIL_TEMPLATE'))
