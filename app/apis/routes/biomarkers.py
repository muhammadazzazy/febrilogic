"""Contain APIs for interacting with biomarkers."""
import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from apis.config import LOINC_FILE
from apis.db.database import Session, get_db
from apis.routes.auth import get_current_user
from apis.models.model import Biomarker

api_router: APIRouter = APIRouter(
    prefix='/api/biomarkers',
    tags=['biomarkers']
)


@api_router.get('')
def get_biomarkers(user: Annotated[dict, Depends(get_current_user)],
                   db: Session = Depends(get_db)) -> dict[str, list[dict[str, str]]]:
    """Fetch all biomarkers from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    results: list[Biomarker] = db.query(Biomarker).all()
    biomarkers: list[dict[str, str]] = []
    for result in results:
        if result.name:
            biomarkers.append({
                'name': result.name,
                'abbreviation': result.abbreviation,
                'unit': result.unit,
                'reference_range': result.reference_range
            })
        else:
            biomarkers.append({
                'abbreviation': result.abbreviation,
                'unit': result.unit,
                'reference_range': result.reference_range
            })
    return {
        'biomarkers': biomarkers
    }


@api_router.get('/units')
def get_biomarker_units(biomarkers: list[str],
                        user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Get the units for all biomarkers."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    if not LOINC_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Loinc.csv file not found.')
    biomarker_units: dict[str, list[str]] = {}
    loinc_df = pd.read_csv(LOINC_FILE, dtype=str, low_memory=False)
    loinc_df['component'] = loinc_df['COMPONENT'].str.lower()
    loinc_df['component_clean'] = loinc_df['component'].str.lower().str.strip()
    for biomarker in biomarkers:
        biomarker_clean = biomarker.lower().strip()
        matches = loinc_df[loinc_df['component_clean'].str.contains(
            biomarker_clean, na=False)]
        if not matches.empty:
            units = matches['EXAMPLE_UCUM_UNITS'].dropna().unique().tolist()
            biomarker_units[biomarker] = units if units else []
        else:
            biomarker_units[biomarker] = []
    invalid_patterns: list[str] = [
        r"\{.*?\}",
        r"[a-zA-Z]*score",
        r"index", r"ratio",
        r"arb", r"titer",
        r"[{}]",
        r"\[.*?\]",
    ]
    for biomarker, units in biomarker_units.items():
        valid_units = [unit for unit in units if not any(
            re.search(pattern, unit) for pattern in invalid_patterns)]
        if valid_units:
            biomarker_units[biomarker] = valid_units
        else:
            biomarker_units[biomarker] = []
    return {'biomarker_units':
            biomarker_units}
