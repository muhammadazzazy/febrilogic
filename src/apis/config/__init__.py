"""Configure settings for the FastAPI application."""
import os

from pathlib import Path
from typing import Final
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

DISEASE_BIOMARKER_FILE: Final[Path] = Path(
    os.environ.get('DISEASE_BIOMARKER_FILE')
)

FAST_API_HOST: Final[str] = os.environ.get('FAST_API_HOST', '0.0.0.0')

FAST_API_PORT: Final[int] = int(os.environ.get('FAST_API_PORT', 8000))


PATIENT_SCHEMA_FILE: Final[Path] = Path(
    os.environ.get('SCHEMA_FILE')
)

PATIENT_DATABASE_FILE: Final[Path] = Path(
    os.environ.get('PATIENT_DATABASE_FILE')
)

SYMPTOM_DEFINITIONS_FILE: Final[Path] = Path(
    os.environ.get('SYMPTOM_DEFINITIONS_FILE')
)

SYMPTOMS_FILE: Final[Path] = Path(
    os.environ.get('SYMPTOMS_FILE')
)
