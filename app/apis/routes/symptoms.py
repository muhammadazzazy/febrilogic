"""Fetch symptom definitions, symptoms, and diseases."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from apis.routes.auth import get_current_user
from apis.services.symptoms import get_symptom_definitions

api_router: APIRouter = APIRouter(
    prefix='/api/symptoms',
    tags=['symptoms']
)


@api_router.get('/categories-definitions')
def get_definitions(user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Fetch symptom definitions from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'category_symptom_definition': get_symptom_definitions()
    }
