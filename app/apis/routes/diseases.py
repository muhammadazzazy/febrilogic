"""Contain APIs for interacting with biomarkers."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apis.db.database import Session, get_db
from apis.routes.auth import get_current_user
from apis.models.model import Disease

api_router: APIRouter = APIRouter(
    prefix='/api/diseases',
    tags=['diseases']
)


@api_router.get('')
def get_patient_negative_diseases(
    user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> dict[str, list[str]]:
    """Get diseases stored in the database."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")
    diseases: list[str] = [name for (name,) in db.query(Disease.name).all()]
    return {
        'diseases': diseases
    }
