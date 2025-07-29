import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
from pandas import DataFrame

from apis.config import DISEASE_BIOMARKER_FILE
from apis.routes.auth import get_current_user
from apis.config import LOINC_FILE

api_router: APIRouter = APIRouter(
    prefix='/api/biomarkers',
    tags=['biomarkers']
)


@api_router.get('')
def get_biomarkers(user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Fetch biomarkers from the corresponding private CSV file."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    if not DISEASE_BIOMARKER_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Biomarker file not found.')

    biomarker_stats_df: DataFrame = pd.read_csv(
        filepath_or_buffer=DISEASE_BIOMARKER_FILE)
    biomarker_stats_df['disease'] = biomarker_stats_df['disease'].astype(
        str).str.strip()
    return {
        'biomarkers': biomarker_stats_df.to_dict(orient='records'),
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
            biomarker_units[biomarker] = units if units else ['No units']
        else:
            biomarker_units[biomarker] = ['No units']
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
            biomarker_units[biomarker] = ['Invalid unit']
    return {'biomarker_units':
            biomarker_units}
