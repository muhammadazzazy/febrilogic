"""Contain APIs for interacting with biomarkers."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from apis.db.database import Session, get_db
from apis.routes.auth import get_current_user
from apis.models.model import Disease, patient_negative_diseases
from apis.models.patient_negative_diseases_request import PatientNegativeDiseasesRequest

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


@api_router.post('')
def add_patient_negative_diseases(
    request: PatientNegativeDiseasesRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Add negative disease for a patient."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed.")
    disease_ids: list[int] = db.scalars(
        select(Disease.id).where(Disease.name.in_(request.negative_diseases))).all()
    data: list[dict[str, Any]] = []
    for disease_id in disease_ids:
        data.append({
            'patient_id': request.patient_id,
            'disease_id': disease_id
        })
    db.execute(patient_negative_diseases.insert(), data)
    db.commit()
    return {
        'patient_id': request.patient_id,
        'negative_diseases': request.negative_diseases
    }
