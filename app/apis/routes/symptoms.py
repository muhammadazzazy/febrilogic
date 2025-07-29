"""Fetch symptom definitions, symptoms, and diseases."""
import csv
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pandas import DataFrame
from sqlalchemy.orm import Session


from apis.config import SYMPTOMS_FILE, SYMPTOM_DEFINITIONS_FILE
from apis.db.database import get_db
from apis.models.create_symptom_request import CreateSymptomRequest
from apis.models.patients import Patients
from apis.models.symptoms import Symptoms

api_router: APIRouter = APIRouter(
    prefix='/api/symptoms',
    tags=['symptoms']
)


@api_router.get('-diseases')
def get_symptoms() -> dict[str, Any]:
    """Fetch symptoms and diseases from the API."""
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
    api_router.state.symptoms = symptoms
    api_router.state.diseases = diseases
    return {
        'symptoms': symptoms,
        'diseases': list(diseases.keys())
    }


@api_router.get('/definitions')
def get_definitions() -> dict[str, Any]:
    """Fetch symptom definitions from the corresponding public CSV file."""
    if not SYMPTOM_DEFINITIONS_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Symptom definitions file not found.')
    try:
        symptom_definitions: DataFrame = pd.read_csv(
            filepath_or_buffer=SYMPTOM_DEFINITIONS_FILE)
        symptom_definitions['symptom'] = symptom_definitions['Symptoms'].astype(
            str).str.strip()
        symptom_definitions['definition'] = \
            symptom_definitions['Definitions needed to be written'].astype(
                str).str.strip()
        symptom_definitions.sort_values(by='symptom', inplace=True)
        symptom_definitions.replace(to_replace='nan', value='', inplace=True)
        return {
            'symptom_definitions': symptom_definitions.set_index('symptom').to_dict()['definition']
        }
    except KeyError as e:
        raise HTTPException(status_code=400,
                            detail=f'Invalid format in symptom definitions file: {e}') from e


@api_router.post('')
def upload_patient_symptoms(create_symptom_request: CreateSymptomRequest,
                            db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload patient symptoms to the database."""
    patient_ids: list[int | None] = []
    patient_ids.append(
        db.query(Patients.id).order_by(Patients.id.desc()).limit(1).scalar()
    )
    patient_ids.append(db.query(Symptoms.patient_id).order_by(
        Symptoms.patient_id.desc()).limit(1).scalar())
    if patient_ids[0] and patient_ids[1]:
        if patient_ids[0] - patient_ids[1] != 1:
            raise HTTPException(
                status_code=400,
                detail='No patient information found. Please submit patient information first.'
            )
    if not patient_ids[0]:
        raise HTTPException(
            status_code=400,
            detail='No patient information found. Please submit patient information first.'
        )
    create_symptom_model: Symptoms = Symptoms(
        patient_id=patient_ids[0],
        abdominal_pains=create_symptom_request.abdominal_pains,
        acholic_stool=create_symptom_request.acholic_stool,
        anorexia=create_symptom_request.anorexia,
        arthralgia=create_symptom_request.arthralgia,
        back_pain=create_symptom_request.back_pain,
        blurred_vision=create_symptom_request.blurred_vision,
        bradycardia=create_symptom_request.bradycardia,
        chest_pain=create_symptom_request.chest_pain,
        chills_and_rigors=create_symptom_request.chills_and_rigors,
        choluria=create_symptom_request.choluria,
        confusion_altered_mental_status=create_symptom_request.confusion_altered_mental_status,
        constipation=create_symptom_request.constipation,
        cough=create_symptom_request.cough,
        dehydration=create_symptom_request.dehydration,
        diarrhea=create_symptom_request.diarrhea,
        dizziness=create_symptom_request.dizziness,
        dyspnea_wheezing_respiratorydistress=create_symptom_request.dyspnea_wheezing_respiratorydistress,
        edema=create_symptom_request.edema,
        eschar=create_symptom_request.eschar,
        eye_symptoms_conjunctivitis_conjunctival_suffusion=create_symptom_request.eye_symptoms_conjunctivitis_conjunctival_suffusion,
        facial_redness=create_symptom_request.facial_redness,
        fatigue=create_symptom_request.fatigue,
        headache=create_symptom_request.headache,
        hematemesis=create_symptom_request.hematemesis,
        hematuria=create_symptom_request.hematuria,
        hemoptysis=create_symptom_request.hemoptysis,
        hemorrhage=create_symptom_request.hemorrhage,
        hepatomegaly=create_symptom_request.hepatomegaly,
        itching=create_symptom_request.itching,
        jaundice=create_symptom_request.jaundice,
        lethargy_drowsiness=create_symptom_request.lethargy_drowsiness,
        lymphadenopathy=create_symptom_request.lymphadenopathy,
        lymphangitis=create_symptom_request.lymphangitis,
        melena=create_symptom_request.melena,
        mouth_ulcers=create_symptom_request.mouth_ulcers,
        mucosal_bleeding=create_symptom_request.mucosal_bleeding,
        myalgia=create_symptom_request.myalgia,
        nausea=create_symptom_request.nausea,
        oliguria=create_symptom_request.oliguria,
        petechia=create_symptom_request.petechia,
        pneumonia=create_symptom_request.pneumonia,
        positive_tourniquet_test=create_symptom_request.positive_tourniquet_test,
        prostration=create_symptom_request.prostration,
        purpura=create_symptom_request.purpura,
        rash=create_symptom_request.rash,
        retro_orbital_pain=create_symptom_request.retro_orbital_pain,
        rhinorrhea=create_symptom_request.rhinorrhea,
        seizures=create_symptom_request.seizures,
        shock=create_symptom_request.shock,
        sore_throat=create_symptom_request.sore_throat,
        splenomegaly=create_symptom_request.splenomegaly,
        tachycardia=create_symptom_request.tachycardia,
        vomiting=create_symptom_request.vomiting,
        weakness_malaise=create_symptom_request.weakness_malaise
    )
    db.add(create_symptom_model)
    db.commit()
    db.refresh(create_symptom_model)
    return {
        'message': 'Patient symptoms uploaded successfully.',
        'patient_id': create_symptom_model.patient_id
    }
