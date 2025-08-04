"""Insert, update, and retrieve patient information."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

from apis.routes.auth import get_current_user
from apis.db.database import get_db
from apis.models.model import (
    Biomarker, Disease, Patient, Symptom,
    patient_biomarkers, patient_negative_diseases, patient_symptoms
)
from apis.models.patient_negative_diseases_request import PatientNegativeDiseasesRequest
from apis.models.patient_request import PatientRequest
from apis.models.patient_biomarkers_request import PatientBiomarkersRequest
from apis.models.symptom_request import SymptomRequest

api_router: APIRouter = APIRouter(
    prefix='/api/patients'
)


@api_router.post('')
def upload_patient_data(patient_request: PatientRequest,
                        user: Annotated[dict, Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient personal information to the SQLite database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    patient_ids: list[int | None] = []
    patient_ids.append(
        db.query(Patient.id).order_by(Patient.id.desc()).limit(1).scalar()
    )
    patient_ids.append(db.query(patient_symptoms.c.patient_id).order_by(
        db.query(patient_symptoms.c.patient_id.desc())).limit(1).scalar())
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
    user_patients: list[Patient] = db.query(
        Patient).filter(Patient.user_id == user['id']).all()
    if not user_patients:
        raise HTTPException(status_code=404,
                            detail='No patients found.')
    patients: list[dict[str, Any]] = []
    for patient in user_patients:
        patients.append({
            'age': patient.age,
            'city': patient.city,
            'country': patient.country,
            'id': patient.id,
            'race': patient.race,
            'sex': patient.sex
        })
    return {
        'patients': patients
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
    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
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


@api_router.post('/{patient_id}/diseases')
def add_patient_negative_diseases(
    patient_id: int,
    request: PatientNegativeDiseasesRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Add negative disease for a patient."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed.")
    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to update this patient.')
    disease_ids: list[int] = db.scalars(
        select(Disease.id).where(Disease.name.in_(request.negative_diseases))).all()
    data: list[dict[str, Any]] = []
    for disease_id in disease_ids:
        data.append({
            'patient_id': patient_id,
            'disease_id': disease_id
        })
    db.execute(patient_negative_diseases.insert(), data)
    db.commit()
    return {
        'patient_id': patient_id,
        'negative_diseases': request.negative_diseases
    }


@api_router.post('/{patient_id}/biomarkers')
def upload_patient_biomarkers(
    patient_id: int,
    patient_biomarkers_request: PatientBiomarkersRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Upload patient biomarkers to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    biomarker_values: dict[str, float] = \
        patient_biomarkers_request.biomarker_values

    data: list = []
    for biomarker, value in biomarker_values.items():
        db_biomarker = db.query(Biomarker).filter(
            Biomarker.abbreviation == biomarker).first()
        if db_biomarker is None:
            raise HTTPException(status_code=404,
                                detail=f'{biomarker} biomarker not found.')
        data.append({
            'patient_id': patient_id,
            'biomarker_id': db_biomarker.id,
            'value': value
        })
    db.execute(patient_biomarkers.insert(), data)
    db.commit()
    return {
        'patient_id': patient_id,
        'message': 'Patient biomarkers uploaded successfully.'
    }


@api_router.post('/{patient_id}/symptoms')
def upload_patient_symptoms(patient_id: int, symptom_request: SymptomRequest,
                            user: Annotated[dict, Depends(get_current_user)],
                            db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient symptoms to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to update this patient.')
    symptom_names: list[str] = symptom_request.symptom_names
    symptoms: list[int] = db.query(Symptom.id).filter(
        Symptom.name.in_(symptom_names)
    ).all()
    symptom_ids = [row[0]
                   for row in symptoms]
    insert_data = [
        {'patient_id': patient_id, 'symptom_id': sid}
        for sid in symptom_ids
    ]
    db.execute(patient_symptoms.insert(), insert_data)
    db.commit()
    return {
        'message': 'Patient symptoms uploaded successfully.',
        'patient_id': patient_id,
        'symptom_ids': symptom_ids
    }
