"""Contain APIs for interacting with biomarkers."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apis.routes.auth import get_current_user
from apis.services.biomarkers import fetch_biomarkers, fetch_biomarker_units


api_router: APIRouter = APIRouter(
    prefix='/api/biomarkers',
    tags=['biomarkers']
)


@api_router.get('')
def get_biomarkers(
        user: Annotated[dict, Depends(get_current_user)],
        biomarkers: Annotated[list[dict[str, str]], Depends(fetch_biomarkers)]
) -> dict[str, list[dict[str, str]]]:
    """Fetch cached biomarkers."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'biomarkers': biomarkers
    }


@api_router.get('/units')
def get_biomarker_units(
        user: Annotated[dict, Depends(get_current_user)],
        biomarker_units: Annotated[dict[str, list[str]], Depends(
            fetch_biomarker_units)]
) -> dict[str, dict[str, list[str]]]:
    """Fetch cached biomarker units."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'biomarker_units': biomarker_units
    }
