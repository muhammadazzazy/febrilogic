"""Insert, update, and retrieve patient information."""
from typing import Annotated, Any

import json
import requests
from fastapi import APIRouter, Depends, HTTPException
from groq import Groq
from pandas import DataFrame
from sqlalchemy import func
from sqlalchemy.orm import Session

from apis.config import (
    GROQ_API_KEY, GROQ_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL,
    OPENROUTER_CONNECT_TIMEOUT, OPENROUTER_READ_TIMEOUT,
    STREAMLIT_BASE_URL
)
from apis.db.database import get_db
from apis.db.patients import get_latest_lab_results
from apis.models.biomarker import BiomarkerInfo
from apis.models.model import (
    Patient, patient_biomarkers, patient_negative_diseases, patient_symptoms
)
from apis.models.patient import (
    PatientBiomarkersRequest, PatientNegativeDiseasesRequest, PatientRequest, PatientSymptomsRequest
)
from apis.routes.auth import get_current_user
from apis.services.biomarkers import fetch_biomarker_stats, fetch_biomarker_catalog
from apis.services.diseases import fetch_diseases
from apis.services.symptoms import fetch_symptom_ids
from apis.tools.afi_model import calculate_probabilities
from apis.tools.prompt import build_prompt

api_router: APIRouter = APIRouter(
    prefix='/api/patients'
)


@api_router.post('')
def upload_patient_data(patient_request: PatientRequest,
                        user: Annotated[dict[str, str | int], Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient information to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
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
        'message': 'Patient data uploaded successfully',
        'patient_id': patient.id
    }


@api_router.get('')
def get_patient_info(user: Annotated[dict[str, str | int], Depends(get_current_user)],
                     db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    """Get patient information based on the authenticated user."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    patient_number = func.row_number().over(
        partition_by=Patient.user_id,
        order_by=Patient.id
    ).label('patient_number')

    user_patients = (
        db.query(Patient, patient_number)
        .filter(Patient.user_id == user['id'])
        .all()
    )

    patients: list[dict[str, Any]] = []

    for patient, number in user_patients:
        patients.append({
            'patient_number': number,
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
                        user: Annotated[dict[str, str | int], Depends(get_current_user)],
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Update patient information in the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    patient: Patient | None = db.query(Patient).filter(Patient.id == patient_id,
                                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to update this patient')
    patient.age = patient_request.age
    patient.city = patient_request.city
    patient.country_id = patient_request.country_id
    patient.race = patient_request.race
    patient.sex = patient_request.sex
    db.commit()
    return {
        'message': 'Patient information updated successfully',
        'patient_id': patient_id
    }


@api_router.post('/{patient_id}/diseases')
def upload_patient_negative_diseases(
    patient_id: int,
    request: PatientNegativeDiseasesRequest,
    user: Annotated[dict[str, str | int], Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Add diseases that the patient tested negative for."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed")

    patient: Patient | None = db.query(Patient).filter(Patient.id == patient_id,
                                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(
            status_code=403,
            detail='Not enough permissions to add negative diseases for this patient'
        )
    disease_names: set[str] = set(request.negative_diseases)
    diseases: dict[str, int] = fetch_diseases()
    disease_ids: list[int] = [
        id_ for name, id_ in diseases.items()
        if name in disease_names
    ]
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


@api_router.post('/{patient_id}/symptoms')
def upload_patient_symptoms(patient_id: int, symptom_request: PatientSymptomsRequest,
                            user: Annotated[dict[str, str | int], Depends(get_current_user)],
                            db: Session = Depends(get_db),
                            symptoms: dict[str, int] = Depends(
                                fetch_symptom_ids)) -> dict[str, Any]:
    """Upload patient symptoms to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    patient: Patient | None = db.query(Patient).filter(Patient.id == patient_id,
                                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to add symptoms for this patient')
    symptom_names: list[str] = symptom_request.symptom_names
    symptom_ids: list[int] = [
        symptoms[name] for name in symptom_names
        if name in symptoms
    ]
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
        'message': 'Patient symptoms uploaded successfully',
        'patient_id': patient_id,
        'symptom_ids': symptom_ids
    }


@api_router.post('/{patient_id}/biomarkers')
def upload_patient_biomarkers(
    patient_id: int,
    request: PatientBiomarkersRequest,
    user: Annotated[dict[str, str | int], Depends(get_current_user)],
    db: Session = Depends(get_db),
    catalog: dict[str, BiomarkerInfo] = Depends(
        fetch_biomarker_catalog)
) -> dict[str, Any]:
    """Upload patient biomarkers to the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')

    patient: Patient | None = db.query(Patient).filter(Patient.id == patient_id,
                                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to add biomarkers for this patient')

    biomarker_value_unit: dict[str, tuple[float, str]
                               ] = request.biomarker_value_unit
    pairs: list[tuple[str, str]] = [
        (abbrev, unit) for abbrev, (_, unit) in request.biomarker_value_unit.items()
    ]
    biomarker_ids: dict[str, int] = {a: catalog[a].id for a, u in pairs
                                     if a in catalog and u in catalog[a].units}
    biomarker_factors: dict[str, float] = {a: catalog[a].units[u]
                                           for a, u in pairs
                                           if a in catalog and u in catalog[a].units}
    data: list[dict[str, Any]] = []
    for biomarker, (value, _) in biomarker_value_unit.items():
        data.append(
            {
                'patient_id': patient_id,
                'biomarker_id': biomarker_ids.get(biomarker),
                'value': value * biomarker_factors.get(biomarker, 1.0)
            }
        )
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
        'message': 'Patient biomarkers uploaded successfully'
    }


@api_router.get('/{patient_id}/calculate')
def calculate(patient_id: int, user: Annotated[dict[str, str | int], Depends(get_current_user)],
              biomarker_df: Annotated[DataFrame, Depends(fetch_biomarker_stats)],
              db: Session = Depends(get_db)) -> dict[str, Any]:
    """Calculate disease probabilities based on patient symptoms and biomarkers."""
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    patient: Patient | None = db.query(Patient).filter(Patient.id == patient_id,
                                                       Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to access this patient')

    lab_results: dict[str, Any] = get_latest_lab_results(
        patient_id=patient_id, db=db)

    negative_diseases: list[str] = lab_results.get('negative_diseases', [])
    print(f'Negative diseases: {negative_diseases}')

    positive_symptoms: list[str] = lab_results.get('symptoms', [])
    print(f'Positive symptoms: {positive_symptoms}')

    biomarker_result = lab_results.get('biomarkers', {})
    print(f'Biomarker results: {biomarker_result}')

    biomarker_row: dict[str, float] = {
        row.abbreviation: row.value for row in biomarker_result}

    calculated_probs = calculate_probabilities(
        negative_diseases=negative_diseases,
        positive_symptoms=positive_symptoms,
        biomarker_row=biomarker_row,
        biomarker_df=biomarker_df
    )

    sym_probs = calculated_probs.get('symptom_probabilities', [])
    bio_probs = calculated_probs.get('symptom_biomarker_probabilities', [])

    return {
        'negative_diseases': negative_diseases,
        'symptoms': positive_symptoms,
        'biomarkers': biomarker_row,
        'symptom_probabilities': sym_probs,
        'symptom_biomarker_probabilities': bio_probs
    }


@api_router.post('/{patient_id}/generate/groq')
def generate_groq(patient_id: int, disease_probabilities: dict[str, Any],
                  user: Annotated[dict[str, str | int], Depends(get_current_user)],
                  db: Session = Depends(get_db)) -> dict[str, str]:
    """Generate an LLM response using Groq."""
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')

    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to access this patient')

    lab_results: dict[str, Any] = get_latest_lab_results(
        patient_id=patient_id, db=db)
    rendered_prompt: str = build_prompt(
        patient=patient, lab_results=lab_results, disease_probabilities=disease_probabilities)
    client: Groq = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                'role': 'user',
                'content': rendered_prompt
            }
        ]
    )
    choice = getattr(response, 'choices', [None])[0] if getattr(
        response, 'choices', None) else None
    content: str | None = getattr(getattr(choice, 'message', None),
                                  'content', None) if choice else None
    if content:
        return {
            'content': content
        }
    raise HTTPException(
        status_code=500, detail='Invalid response from Groq API')


@api_router.post('/{patient_id}/generate/openrouter')
def generate_openrouter(
        patient_id: int, disease_probabilities: dict,
        user: Annotated[dict[str, str | int], Depends(get_current_user)],
        db: Session = Depends(get_db)) -> dict[str, str]:
    """Generate an LLM response based on calculated disease probabilities."""
    if not user:
        raise HTTPException(status_code=401, detail='Authentication failed')

    patient: Patient = db.query(Patient).filter(Patient.id == patient_id,
                                                Patient.user_id == user['id']).first()
    if not patient:
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to access this patient')

    headers: dict[str, str] = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': STREAMLIT_BASE_URL,
        'X-Title': 'FebriLogic'
    }
    lab_results: dict[str, Any] = get_latest_lab_results(
        patient_id=patient_id, db=db)
    rendered_prompt: str = build_prompt(
        patient=patient, lab_results=lab_results, disease_probabilities=disease_probabilities)
    data: dict[str, str] = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': rendered_prompt
            }
        ]
    }
    response = requests.post(
        url=OPENROUTER_URL,
        headers=headers, data=json.dumps(data),
        timeout=(OPENROUTER_CONNECT_TIMEOUT, OPENROUTER_READ_TIMEOUT)
    )
    choices: list[dict[str, Any]] = response.json().get('choices', [])
    if not choices:
        raise HTTPException(status_code=500,
                            detail='No choices returned from OpenRouter API')
    if 'message' not in choices[0]:
        raise HTTPException(status_code=500,
                            detail='No message in the response from OpenRouter API')
    message: dict[str, Any] = choices[0].get('message', {})
    if 'content' not in message:
        raise HTTPException(status_code=500,
                            detail='No content in the response from OpenRouter API')
    content = message.get('content', '')
    return {
        'content': content
    }
