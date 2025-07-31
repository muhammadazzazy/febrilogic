"""Configure settings for the FastAPI application."""
import os

from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parents[3]

FAST_API_HOST: Final[str] = os.environ.get('FAST_API_HOST', '0.0.0.0')

FAST_API_PORT: Final[int] = int(os.environ.get('FAST_API_PORT', 8000))

ALGORITHM: Final[str] = os.environ.get('ALGORITHM', 'HS256')

SECRET_KEY: Final[str] = os.environ.get('SECRET_KEY')

ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = int(
    os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

DISEASE_BIOMARKER_FILE: Final[Path] = BASE_DIR / Path(
    os.environ.get('DISEASE_BIOMARKER_FILE')
)

SYMPTOMS_FILE: Final[Path] = BASE_DIR / Path(
    os.environ.get('SYMPTOMS_FILE')
)

LOINC_FILE: Final[Path] = BASE_DIR / Path(
    os.environ.get('LOINC_FILE'))

SQLALCHEMY_DATABASE_URL: Final[str] = 'sqlite:///' + \
    str(BASE_DIR / os.environ.get('DATABASE_FILE'))
