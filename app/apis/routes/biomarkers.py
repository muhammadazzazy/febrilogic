"""Contain APIs for interacting with biomarkers."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from apis.db.database import Session, get_db
from apis.routes.auth import get_current_user
from apis.models.model import Biomarker, Unit, biomarker_units

api_router: APIRouter = APIRouter(
    prefix='/api/biomarkers',
    tags=['biomarkers']
)


@api_router.get('/units')
def get_biomarker_units(user: Annotated[dict, Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, dict[str, list[str]]]:
    """Fetch all biomarker units from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
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

    return {
        'biomarker_units': biomarker_mapping
    }


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
                'standard_unit': result.standard_unit,
                'reference_range': result.reference_range
            })
        else:
            biomarkers.append({
                'abbreviation': result.abbreviation,
                'standard_unit': result.standard_unit,
                'reference_range': result.reference_range
            })
    return {
        'biomarkers': biomarkers
    }
