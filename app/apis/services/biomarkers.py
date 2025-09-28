"""Service to handle biomarker statistics."""
from functools import lru_cache

import pandas as pd
from pandas import DataFrame


from apis.config import BIOMARKER_STATS_FILE
from apis.db.database import SessionLocal
from apis.models.model import Biomarker, biomarker_units, Unit


@lru_cache(maxsize=1)
def get_biomarker_stats() -> DataFrame:
    """Get cached biomarker statistics dataframe."""
    biomarker_df: DataFrame = pd.read_csv(BIOMARKER_STATS_FILE)
    biomarker_df['disease'] = biomarker_df['disease'].astype(str).str.strip()
    return biomarker_df


@lru_cache(maxsize=1)
def fetch_biomarkers() -> list[dict[str, str]]:
    """Fetch all biomarkers from the database."""
    with SessionLocal() as db:
        results: list[Biomarker] = db.query(Biomarker).all()
    biomarkers: list[dict[str, str]] = []
    for result in results:
        if result.name:
            biomarkers.append({
                'name': result.name,
                'abbreviation': result.abbreviation,
                'standard_unit': result.standard_unit,
                'reference_range': result.reference_range
            })
        else:
            biomarkers.append({
                'abbreviation': result.abbreviation,
                'standard_unit': result.standard_unit,
                'reference_range': result.reference_range
            })
    return biomarkers


@lru_cache(maxsize=1)
def fetch_biomarker_units() -> dict[str, dict[str, list[str]]]:
    """Fetch all biomarker units from the database."""
    with SessionLocal() as db:
        results = (
            db.query(Biomarker.abbreviation, Unit.symbol)
            .join(biomarker_units, Biomarker.id == biomarker_units.c.biomarker_id)
            .join(Unit, Unit.id == biomarker_units.c.unit_id)
            .all()
        )
    biomarker_mapping: dict[str, list[str]] = {}
    for abbreviation, symbol in results:
        if abbreviation not in biomarker_mapping:
            biomarker_mapping[abbreviation] = []
        biomarker_mapping[abbreviation].append(symbol)
    return biomarker_mapping
