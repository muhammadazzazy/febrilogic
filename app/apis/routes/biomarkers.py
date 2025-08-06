"""Contain APIs for interacting with biomarkers."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
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
