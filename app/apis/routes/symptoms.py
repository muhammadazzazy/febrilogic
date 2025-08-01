"""Fetch symptom definitions, symptoms, and diseases."""
import csv
from collections import defaultdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from apis.config import SYMPTOMS_FILE
from apis.db.database import get_db
from apis.models.model import Category, Patient, patient_symptoms, Symptom
from apis.models.symptom_request import SymptomRequest
from apis.routes.auth import get_current_user

api_router: APIRouter = APIRouter(
    prefix='/api/symptoms',
    tags=['symptoms']
)


@api_router.get('-diseases')
def get_symptoms(user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Fetch symptoms and diseases from the API."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    if not SYMPTOMS_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Symptoms file not found.')
    with open(file=SYMPTOMS_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        diseases: dict[str, dict[str, float]] = {}
        symptoms: list[str] = []
        for row in reader:
            disease_name: str = row['disease'].strip()
            diseases[disease_name] = {}
            if not symptoms:
                symptoms = [col for col in row.keys() if col != 'disease']
            for symptom in symptoms:
                diseases[disease_name][symptom] = float(row[symptom])
    return {
        'symptoms': symptoms,
        'diseases': list(diseases.keys())
    }


@api_router.get('/categories-definitions')
def get_definitions(user: Annotated[dict, Depends(get_current_user)],
                    db: Session = Depends(get_db)) -> dict[str, Any]:
    """Fetch symptom definitions from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    results = db.query(Category.name, Symptom.name,
                       Symptom.definition).join(Symptom).all()
    category_symptom_definition: defaultdict[str,
                                             list[tuple[str, str]]] = defaultdict(list)
    for category_name, symptom_name, definition in results:
        category_symptom_definition[category_name].append(
            (symptom_name, definition))
    return {
        'category_symptom_definition': category_symptom_definition
    }


@api_router.post('')
def upload_patient_symptoms(symptom_request: SymptomRequest,
                            user: Annotated[dict, Depends(get_current_user)],
                            db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient symptoms to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    patient_ids: list[int | None] = []
    patient_ids.append(
        db.query(Patient.id).order_by(Patient.id.desc()).limit(1).scalar()
    )
    patient_ids.append(symptom_request.patient_id)
    print(patient_ids)
    # if patient_ids[0] and patient_ids[1]:
    #     if patient_ids[0] - patient_ids[1] != 0:
    #         raise HTTPException(
    #             status_code=400,
    #             detail='No patient information found. Please submit patient information first.'
    #         )
    # if not patient_ids[0]:
    #     raise HTTPException(
    #         status_code=400,
    #         detail='No patient information found. Please submit patient information first.'
    #     )
    symptom_names = symptom_request.symptom_names
    symptoms: list[int] = db.query(Symptom.id).filter(
        Symptom.name.in_(symptom_names)
    ).all()
    symptom_ids = [row[0]
                   for row in symptoms]
    insert_data = [
        {'patient_id': patient_ids[0], 'symptom_id': sid}
        for sid in symptom_ids
    ]
    db.execute(patient_symptoms.insert(), insert_data)
    db.commit()
    return {
        'message': 'Patient symptoms uploaded successfully.',
        'patient_id': symptom_request.patient_id,
        'symptom_ids': symptom_ids
    }
