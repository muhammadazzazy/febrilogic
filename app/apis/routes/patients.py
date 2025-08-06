"""Insert, update, and retrieve patient information."""
from typing import Annotated, Any

import json
import pandas as pd
import requests
from fastapi import APIRouter, Depends, HTTPException
from pandas import DataFrame
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from apis.config import (
    BIOMARKER_STATS_FILE, SYMPTOM_WEIGHTS_FILE,
    GROQ_API_KEY, GROQ_MODEL, GROQ_URL, GROQ_CONNECT_TIMEOUT, GROQ_READ_TIMEOUT,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL, OPENROUTER_CONNECT_TIMEOUT, OPENROUTER_READ_TIMEOUT
)
from apis.db.database import get_db
from apis.models.model import (
    Biomarker, Disease, Patient, Symptom,
    patient_biomarkers, patient_negative_diseases, patient_symptoms
)
from apis.models.patient_negative_diseases_request import PatientNegativeDiseasesRequest
from apis.models.patient_request import PatientRequest
from apis.models.patient_biomarkers_request import PatientBiomarkersRequest
from apis.models.symptom_request import SymptomRequest
from apis.routes.auth import get_current_user
from apis.tools.afi_model import (
    calculate_disease_scores, softmax, load_disease_data,
    expand_diseases_for_severity, update_with_all_biomarkers
)


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
        country_id=patient_request.country_id,
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
    patients: list[dict[str, Any]] = []
    for patient in user_patients:
        patients.append({
            'age': patient.age,
            'city': patient.city,
            'country_id': patient.country_id,
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
    patient.country_id = patient_request.country_id
    patient.race = patient_request.race
    patient.sex = patient_request.sex
    db.commit()
    return {
        'message': 'Patient information updated successfully.',
        'patient_id': patient_id
    }


@api_router.post('/{patient_id}/diseases')
def upload_patient_negative_diseases(
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
    if not data:
        data.append({
            'patient_id': patient_id,
            'disease_id': None
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

    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to update this patient.')

    biomarker_values: dict[str, float] = \
        patient_biomarkers_request.biomarker_values

    abbreviations: list[str] = list(biomarker_values.keys())
    biomarkers = db.query(Biomarker).filter(
        Biomarker.abbreviation.in_(abbreviations)).all()
    biomarker_map: dict[str, int] = {
        b.abbreviation: b.id for b in biomarkers
    }

    data: list[dict[str, int | float | None]] = []
    for abbreviation, value in biomarker_values.items():
        biomarker_id = biomarker_map.get(abbreviation)
        data.append({
            'patient_id': patient_id,
            'biomarker_id': biomarker_id,
            'value': value
        })
    if not data:
        data.append({
            'patient_id': patient_id,
            'biomarker_id': None,
            'value': None
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
    data: list[dict[str, int | None]] = [
        {'patient_id': patient_id, 'symptom_id': sid}
        for sid in symptom_ids
    ]
    if not data:
        data.append({
            'patient_id': patient_id,
            'symptom_id': None
        })
    db.execute(patient_symptoms.insert(), data)
    db.commit()
    return {
        'message': 'Patient symptoms uploaded successfully.',
        'patient_id': patient_id,
        'symptom_ids': symptom_ids
    }


@api_router.get('/{patient_id}/calculate')
def calculate(patient_id: int, user: Annotated[dict, Depends(get_current_user)],
              db: Session = Depends(get_db)) -> dict[str, Any]:
    """Calculate disease probabilities based on patient symptoms and biomarkers."""
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed.')

    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to access this patient.')

    latest_datetime = db.execute(
        select(patient_negative_diseases.c.created_at)
        .where(patient_negative_diseases.c.patient_id == patient_id)
        .order_by(patient_negative_diseases.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    print(f'Latest datetime for negative diseases: {latest_datetime}')

    negative_diseases: list[str] = [
        row.name for row in db.query(Disease.name)
        .join(patient_negative_diseases)
        .filter(patient_negative_diseases.c.patient_id == patient_id,
                func.strftime('%Y-%m-%d %H:%M:%S', patient_negative_diseases.c.created_at) == func.strftime('%Y-%m-%d %H:%M:%S', latest_datetime)).all()
    ]
    print(f'Latest negative diseases: {negative_diseases}')

    diseases, symptoms = load_disease_data(
        filepath=SYMPTOM_WEIGHTS_FILE, negative_diseases=negative_diseases)

    print(f'Diseases loaded: {list(diseases.keys())}')
    biomarker_df: DataFrame = pd.read_csv(BIOMARKER_STATS_FILE)
    biomarker_df['disease'] = biomarker_df['disease'].astype(str).str.strip()
    latest_datetime = db.execute(
        select(patient_symptoms.c.created_at)
        .where(patient_symptoms.c.patient_id == patient_id)
        .order_by(patient_symptoms.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    print(f'Latest datetime for positive symptoms: {latest_datetime}')
    positive_symptoms: list[str] = [
        row.name for row in db.query(Symptom.name)
        .join(patient_symptoms)
        .filter(patient_symptoms.c.patient_id == patient_id,
                func.strftime('%Y-%m-%d %H:%M:%S', patient_symptoms.c.created_at) == func.strftime('%Y-%m-%d %H:%M:%S', latest_datetime)).all()
    ]
    print(f'Latest positive symptoms: {positive_symptoms}')
    disease_scores = calculate_disease_scores(diseases=diseases, symptoms=symptoms,
                                              positive_symptoms=positive_symptoms)
    disease_sums = {disease: sum(scores)
                    for disease, scores in disease_scores.items()}
    disease_names: list[str] = list(disease_sums.keys())
    disease_values: list[float] = list(disease_sums.values())
    prior_probs = softmax(disease_values)
    sym_probs = list(zip(disease_names, prior_probs))
    sym_probs_expanded = expand_diseases_for_severity(sym_probs)
    sym_probs_expanded = sorted(
        sym_probs_expanded, key=lambda x: x[1], reverse=True)
    latest_datetime = db.execute(
        select(patient_biomarkers.c.created_at)
        .where(patient_biomarkers.c.patient_id == patient_id)
        .order_by(patient_biomarkers.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    print(f'Latest datetime for biomarkers: {latest_datetime}')
    biomarker_result = db.query(
        Biomarker.abbreviation,
        patient_biomarkers.c.value
    ).join(
        Biomarker, patient_biomarkers.c.biomarker_id == Biomarker.id).filter(
        patient_biomarkers.c.patient_id == patient_id,
        func.strftime('%Y-%m-%d %H:%M:%S', patient_biomarkers.c.created_at) == func.strftime('%Y-%m-%d %H:%M:%S', latest_datetime)).all()
    print(f'Latest biomarkers: {biomarker_result}')
    biomarker_row: dict[str, float] = {
        row.abbreviation: row.value for row in biomarker_result}

    if biomarker_row:
        bio_probs_vals = update_with_all_biomarkers(
            [d for d, _ in sym_probs_expanded],
            [p for _, p in sym_probs_expanded],
            biomarker_df,
            biomarker_row
        )
        bio_probs = list(
            zip([d for d, _ in sym_probs_expanded], bio_probs_vals))
    else:
        bio_probs = sym_probs_expanded.copy()
    bio_probs = sorted(bio_probs, key=lambda x: x[1], reverse=True)
    return {
        'symptom_probabilities': sym_probs_expanded,
        'symptom_biomarker_probabilities': bio_probs
    }


@api_router.post('/{patient_id}/generate/openrouter')
def generate_openrouter(patient_id: int, disease_probabilities: dict,
                        user: Annotated[dict: [str, Any], Depends(get_current_user)]) -> dict[str, str]:
    """Generate an LLM response based on calculated disease probabilities."""
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed.')
    headers: dict[str, str] = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://febrilogic.com',
        'X-Title': 'FebriLogic'
    }
    symptom_probabilities: list[tuple[str, float]] = disease_probabilities.get(
        'symptom_probabilities', [])
    biomarker_probabilities: list[tuple[str, float]] = disease_probabilities.get(
        'biomarker_probabilities', [])
    data: dict[str, str] = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': f"Given the following disease probabilities for Patient {patient_id} (ratios):\n{json.dumps(symptom_probabilities)}\n\n"
                f"and the following biomarker probabilities (ratios):\n{json.dumps(biomarker_probabilities)}\n\n"
                "What are the top 3 most likely diseases (percentages)? Arrange the top 3 diseases in a numbered list from 1 to 3. Use the biomarker probabilities to make final ranking."
            }
        ]
    }
    response = requests.post(url=OPENROUTER_URL,
                             headers=headers, data=json.dumps(data), timeout=(OPENROUTER_CONNECT_TIMEOUT, OPENROUTER_READ_TIMEOUT))
    choices: list[dict[str, Any]] = response.json().get('choices', [])
    if not choices:
        raise HTTPException(
            status_code=500, detail='No choices returned from OpenRouter API.')
    if 'message' not in choices[0]:
        raise HTTPException(
            status_code=500, detail='No message in the response from OpenRouter API.')
    message: dict[str, Any] = choices[0].get('message', {})
    if 'content' not in message:
        raise HTTPException(
            status_code=500, detail='No content in the response from OpenRouter API.')
    content = message.get('content', '')
    return {
        'content': content
    }


@api_router.post('/{patient_id}/generate/groq')
def generate_groq(patient_id: int, disease_probabilities: dict[str, Any],
                  user: Annotated[dict, Depends(get_current_user)]) -> dict[str, str]:
    """Generate an LLM response using Groq."""
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed.')
    headers: dict[str, str] = {'Authorization': f'Bearer {GROQ_API_KEY}',
                               'Content-Type': 'application/json'}

    symptom_probabilities: list[tuple[str, float]] = disease_probabilities.get(
        'symptom_probabilities', [])
    biomarker_probabilities: list[tuple[str, float]] = disease_probabilities.get(
        'biomarker_probabilities', [])
    data: dict[str, str] = {
        'model': GROQ_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': f"Given the following disease probabilities for Patient {patient_id} (ratios):\n{json.dumps(symptom_probabilities)}\n\n"
                f"and the following biomarker probabilities (ratios):\n{json.dumps(biomarker_probabilities)}\n\n"
                "What are the top 3 most likely diseases (percentages)? Arrange the top 3 diseases in a numbered list from 1 to 3."
            }
        ]
    }
    response = requests.post(url=GROQ_URL,
                             headers=headers, data=json.dumps(data), timeout=(GROQ_CONNECT_TIMEOUT, GROQ_READ_TIMEOUT))
    choices: list[dict[str, Any]] = response.json().get('choices', [])
    if not choices:
        raise HTTPException(
            status_code=500, detail='No choices returned from Groq API.')
    if 'message' not in choices[0]:
        raise HTTPException(
            status_code=500, detail='No message in the response from Groq API.')
    message: dict[str, Any] = choices[0].get('message', {})
    if 'content' not in message:
        raise HTTPException(
            status_code=500, detail='No content in the response from Groq API.')
    content: str = message.get('content', '')
    return {
        'content': content
    }
