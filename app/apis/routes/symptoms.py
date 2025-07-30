"""Fetch symptom definitions, symptoms, and diseases."""
import csv
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pandas import DataFrame
from sqlalchemy.orm import Session


from apis.config import SYMPTOMS_FILE, SYMPTOM_DEFINITIONS_FILE
from apis.db.database import get_db
from apis.models.symptom_request import SymptomRequest
from apis.models.user_patient import Patient
from apis.models.symptom import Symptom
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
    api_router.state.symptoms = symptoms
    api_router.state.diseases = diseases
    return {
        'symptoms': symptoms,
        'diseases': list(diseases.keys())
    }


@api_router.get('/definitions')
def get_definitions(user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Fetch symptom definitions from the corresponding public CSV file."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
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
    patient_ids.append(db.query(Symptom.patient_id).order_by(
        Symptom.patient_id.desc()).limit(1).scalar())
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
    symptoms: Symptom = Symptom(
        patient_id=patient_ids[0],
        abdominal_pains=symptom_request.abdominal_pains,
        acholic_stool=symptom_request.acholic_stool,
        anorexia=symptom_request.anorexia,
        arthralgia=symptom_request.arthralgia,
        back_pain=symptom_request.back_pain,
        blurred_vision=symptom_request.blurred_vision,
        bradycardia=symptom_request.bradycardia,
        chest_pain=symptom_request.chest_pain,
        chills_and_rigors=symptom_request.chills_and_rigors,
        choluria=symptom_request.choluria,
        confusion_altered_mental_status=symptom_request.confusion_altered_mental_status,
        constipation=symptom_request.constipation,
        cough=symptom_request.cough,
        dehydration=symptom_request.dehydration,
        diarrhea=symptom_request.diarrhea,
        dizziness=symptom_request.dizziness,
        dyspnea_wheezing_respiratorydistress=symptom_request.dyspnea_wheezing_respiratorydistress,
        edema=symptom_request.edema,
        eschar=symptom_request.eschar,
        eye_symptoms_conjunctivitis_conjunctival_suffusion=symptom_request.eye_symptoms_conjunctivitis_conjunctival_suffusion,
        facial_redness=symptom_request.facial_redness,
        fatigue=symptom_request.fatigue,
        headache=symptom_request.headache,
        hematemesis=symptom_request.hematemesis,
        hematuria=symptom_request.hematuria,
        hemoptysis=symptom_request.hemoptysis,
        hemorrhage=symptom_request.hemorrhage,
        hepatomegaly=symptom_request.hepatomegaly,
        itching=symptom_request.itching,
        jaundice=symptom_request.jaundice,
        lethargy_drowsiness=symptom_request.lethargy_drowsiness,
        lymphadenopathy=symptom_request.lymphadenopathy,
        lymphangitis=symptom_request.lymphangitis,
        melena=symptom_request.melena,
        mouth_ulcers=symptom_request.mouth_ulcers,
        mucosal_bleeding=symptom_request.mucosal_bleeding,
        myalgia=symptom_request.myalgia,
        nausea=symptom_request.nausea,
        oliguria=symptom_request.oliguria,
        petechia=symptom_request.petechia,
        pneumonia=symptom_request.pneumonia,
        positive_tourniquet_test=symptom_request.positive_tourniquet_test,
        prostration=symptom_request.prostration,
        purpura=symptom_request.purpura,
        rash=symptom_request.rash,
        retro_orbital_pain=symptom_request.retro_orbital_pain,
        rhinorrhea=symptom_request.rhinorrhea,
        seizures=symptom_request.seizures,
        shock=symptom_request.shock,
        sore_throat=symptom_request.sore_throat,
        splenomegaly=symptom_request.splenomegaly,
        tachycardia=symptom_request.tachycardia,
        vomiting=symptom_request.vomiting,
        weakness_malaise=symptom_request.weakness_malaise
    )
    db.add(symptoms)
    db.commit()
    db.refresh(symptoms)
    return {
        'message': 'Patient symptoms uploaded successfully.',
        'patient_id': symptoms.patient_id
    }
