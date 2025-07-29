from typing import Any

from fastapi import APIRouter, HTTPException
import pandas as pd
from pandas import DataFrame

from apis.config import DISEASE_BIOMARKER_FILE

api_router: APIRouter = APIRouter(
    prefix='/api/biomarkers',
    tags=['biomarkers']
)


@api_router.get('/')
def get_biomarkers() -> dict[str, Any]:
    """Fetch biomarkers from the corresponding private CSV file."""
    if not DISEASE_BIOMARKER_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Biomarker file not found.')

    biomarker_stats_df: DataFrame = pd.read_csv(
        filepath_or_buffer=DISEASE_BIOMARKER_FILE)
    biomarker_stats_df['disease'] = biomarker_stats_df['disease'].astype(
        str).str.strip()

    api_router.state.biomarker_stats_df = biomarker_stats_df
    return {
        'biomarkers': biomarker_stats_df.to_dict(orient='records'),
    }
