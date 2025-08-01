"""Upload patient personal data to the database"""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from apis.routes.auth import get_current_user
from apis.db.database import get_db
from apis.models.model import Patient, patient_symptoms
from apis.models.patient_request import PatientRequest

api_router: APIRouter = APIRouter(
    prefix='/api/patient'
)


@api_router.post('')
def upload_patient_data(patient_request: PatientRequest,
                        user: Annotated[dict, Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient personal information to the SQLite database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    print(f'User: {user.items()}')
    patient_ids: list[int | None] = []
    patient_ids.append(
        db.query(Patient.id).order_by(Patient.id.desc()).limit(1).scalar()
    )
    patient_ids.append(db.query(patient_symptoms.c.patient_id).order_by(
        db.query(patient_symptoms.c.patient_id.desc())).limit(1).scalar())
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
    patient = Patient(
        age=patient_request.age,
        city=patient_request.city,
        country=patient_request.country,
        race=patient_request.race,
        sex=patient_request.sex,
        user_id=user['id']
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {
        'message': 'Patient data uploaded successfully.',
        'patient_id': patient.id
    }


@api_router.get('')
def get_patient_info(user: Annotated[dict, Depends(get_current_user)],
                     db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    """Get patient information based on the authenticated user."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    patients = db.query(Patient).filter(Patient.user_id == user['id'])
    if not patients:
        raise HTTPException(status_code=404,
                            detail='No patients found.')
    patients_list: list[dict[str, Any]] = []
    for patient in patients:
        patients_list.append({
            'age': patient.age,
            'city': patient.city,
            'country': patient.country,
            'id': patient.id,
            'race': patient.race,
            'sex': patient.sex
        })
    return {
        'patients': patients_list
    }


@api_router.post('/{patient_id}')
def update_patient_info(patient_id: int,
                        patient_request: PatientRequest,
                        user: Annotated[dict, Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Update patient information in the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    patient = db.query(Patient).filter(Patient.id == patient_id,
                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to update this patient.')
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.user_id == user['id']
    ).first()
    patient.age = patient_request.age
    patient.city = patient_request.city
    patient.country = patient_request.country
    patient.race = patient_request.race
    patient.sex = patient_request.sex
    db.commit()
    return {
        'message': 'Patient information updated successfully.',
        'patient_id': patient_id
    }
