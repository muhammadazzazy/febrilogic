"""Contain APIs for interacting with biomarkers."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apis.routes.auth import get_current_user
from apis.services.diseases import get_diseases

api_router: APIRouter = APIRouter(
    prefix='/api/diseases',
    tags=['diseases']
)


@api_router.get('')
def get_patient_negative_diseases(
        user: Annotated[dict, Depends(get_current_user)]) -> dict[str, list[str]]:
    """Get diseases stored in the database."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")
    return {
        'diseases': get_diseases()
    }
