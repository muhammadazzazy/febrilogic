"""Fetch symptom definitions, symptoms, and diseases."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from apis.routes.auth import get_current_user
from apis.services.symptoms import fetch_symptom_definitions

api_router: APIRouter = APIRouter(
    prefix='/api/symptoms',
    tags=['symptoms']
)


@api_router.get('/categories-definitions')
def get_symptom_definitions(
        user: Annotated[dict[str, str | int], Depends(get_current_user)],
        symptom_definitions: Annotated[dict[str, list[tuple[str, str]]], Depends(
            fetch_symptom_definitions)]
) -> dict[str, Any]:
    """Fetch symptom definitions from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'category_symptom_definition': symptom_definitions
    }
