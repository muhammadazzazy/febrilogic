"""Configuration settings for the FastAPI application."""
import os

from pathlib import Path
from typing import Final
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

SYMPTOMS_FILE_PATH: Final[Path] = Path(
    os.environ.get('SYMPTOMS_FILE_PATH')
)

DISEASE_BIOMARKER_FILE_PATH: Final[Path] = Path(
    os.environ.get('DISEASE_BIOMARKER_FILE_PATH')
)

SYMPTOM_DEFINITIONS_FILE_PATH: Final[Path] = Path(
    os.environ.get('SYMPTOM_DEFINITIONS_FILE_PATH')
)

FAST_API_HOST: Final[str] = os.environ.get('FAST_API_HOST', '0.0.0.0')

FAST_API_PORT: Final[int] = int(os.environ.get('FAST_API_PORT', 8000))
