"""Upload patient personal data to the database"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from apis.db.database import get_db
from apis.models.patients import Patients
from apis.models.symptoms import Symptoms
from apis.models.create_patient_request import CreatePatientRequest


api_router: APIRouter = APIRouter(
    prefix='/api/patient'
)


@api_router.post('')
def upload_patient_data(create_patient_request: CreatePatientRequest,
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient personal information to the SQLite database."""
    patient_ids: list[int | None] = []
    patient_ids.append(
        db.query(Patients.id).order_by(Patients.id.desc()).limit(1).scalar()
    )
    patient_ids.append(db.query(Symptoms.patient_id).order_by(
        Symptoms.patient_id.desc()).limit(1).scalar())
    if (patient_ids[0]) and (patient_ids[1]):
        if patient_ids[0] - patient_ids[1] != 0:
            raise HTTPException(
                status_code=400,
                detail='No patient symptoms found. Please submit patient symptoms first.'
            )
    if (patient_ids[0]) and (not patient_ids[1]):
        raise HTTPException(
            status_code=400,
            detail='No patient symptoms found. Please submit patient symptoms first.'
        )
    create_patient_model = Patients(
        name=create_patient_request.name,
        age=create_patient_request.age,
        race=create_patient_request.race,
        sex=create_patient_request.sex
    )
    db.add(create_patient_model)
    db.commit()
    db.refresh(create_patient_model)
    return {
        'message': 'Patient data uploaded successfully.',
        'patient_id': create_patient_model.id
    }
