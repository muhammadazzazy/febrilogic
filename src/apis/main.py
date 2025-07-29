"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
import sqlite3
from contextlib import asynccontextmanager
from typing import Any

import csv
import pandas as pd
import uvicorn

from fastapi import FastAPI, HTTPException
from pandas import DataFrame

from config import (
    FAST_API_HOST, FAST_API_PORT, DISEASE_BIOMARKER_FILE,
    PATIENT_DATABASE_FILE, PATIENT_SCHEMA_FILE,
    SYMPTOMS_FILE, SYMPTOM_DEFINITIONS_FILE,
)

from model.afi import (
    process_patient_symptoms, diagnose_patient,
    expand_disease_probabilities, get_updated_probs
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application and set up the database."""
    create_schema: bool = not PATIENT_DATABASE_FILE.exists()
    conn = sqlite3.connect(PATIENT_DATABASE_FILE)
    conn.execute('PRAGMA foreign_keys = ON')
    if create_schema:
        with open(PATIENT_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    conn.close()
    yield

api = FastAPI(lifespan=lifespan)

api.state.diseases = None
api.state.symptoms = None
api.state.biomarker_stats_df = None

api.state.patient_data = []

api.state.patient_symptoms = []

api.state.biomarker_df = None

api.state.all_results = None
api.state.per_disease_stats = None


@api.get('/api/diseases-symptoms')
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
    api.state.symptoms = symptoms
    api.state.diseases = diseases
    return {
        'symptoms': symptoms,
        'diseases': list(diseases.keys())
    }


@api.get('/api/symptom-definitions')
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


@api.get('/api/biomarkers')
def get_biomarkers() -> dict[str, Any]:
    """Fetch biomarkers from the corresponding private CSV file."""
    if not DISEASE_BIOMARKER_FILE.exists():
        raise HTTPException(status_code=404,
                            detail='Biomarker file not found.')

    biomarker_stats_df: DataFrame = pd.read_csv(
        filepath_or_buffer=DISEASE_BIOMARKER_FILE)
    biomarker_stats_df['disease'] = biomarker_stats_df['disease'].astype(
        str).str.strip()

    api.state.biomarker_stats_df = biomarker_stats_df
    return {
        'biomarkers': biomarker_stats_df.to_dict(orient='records'),
    }


@api.post('/api/patient')
def upload_patient_data(patient: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Load patient data and biomarkers from the frontend."""
    if not patient.get('patient'):
        raise HTTPException(status_code=404, detail='Patient data not found.')
    api.state.patient_data.append(patient.get('patient', {}))
    conn = sqlite3.connect(PATIENT_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM patients ORDER BY id DESC LIMIT 1'
    )

    patient_ids: list[tuple[int | None]] = []
    patient_ids.append(cursor.fetchone())
    cursor.execute(
        'SELECT patient_id FROM symptoms ORDER BY patient_id DESC LIMIT 1'
    )
    patient_ids.append(cursor.fetchone())
    if (patient_ids[0]) and (patient_ids[1]):
        if patient_ids[0][0] - patient_ids[1][0] != 0:
            raise HTTPException(
                status_code=400,
                detail='No patient symptoms found. Please submit patient symptoms first.'
            )
    if (patient_ids[0]) and (not patient_ids[1]):
        raise HTTPException(
            status_code=400,
            detail='No patient symptoms found. Please submit patient symptoms first.'
        )
    insert_query: str = 'INSERT INTO patients (name, age, sex, race, date) VALUES (?, ?, ?, ?, ?)'
    cursor.execute(
        insert_query,
        (patient['patient']['name'], patient['patient']['age'],
         patient['patient']['sex'], patient['patient']['race'],
         patient['patient']['date'])
    )
    lastrowid: int = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        'message': 'Patient data uploaded successfully.',
        'patient_id': lastrowid
    }


@api.post('/api/symptoms')
def upload_symptoms(patient_symptoms: dict[str, dict[str, bool]]) -> dict[str, Any]:
    """Load symptoms data for a patient."""
    if not patient_symptoms.get('patient_symptoms'):
        raise HTTPException(status_code=404, detail='Patient data not found.')
    conn = sqlite3.connect(PATIENT_DATABASE_FILE)
    cursor = conn.cursor()
    patient_ids: list[tuple[int | None]] = []
    cursor.execute(
        """SELECT id FROM patients ORDER BY id DESC LIMIT 1"""
    )
    patient_ids.append(cursor.fetchone())
    cursor.execute(
        """SELECT patient_id FROM symptoms ORDER BY patient_id DESC LIMIT 1"""
    )
    patient_ids.append(cursor.fetchone())
    if patient_ids[0] and patient_ids[1]:
        if patient_ids[0][0] - patient_ids[1][0] != 1:
            raise HTTPException(
                status_code=400,
                detail='No patient information found. Please submit patient information first.'
            )
    if not patient_ids[0]:
        raise HTTPException(
            status_code=400,
            detail='No patient information found. Please submit patient information first.'
        )
    num_of_symptoms: int = len(patient_symptoms['patient_symptoms'])
    num_of_fields: int = num_of_symptoms + 1
    symptom_flags: list[bool] = list(
        patient_symptoms['patient_symptoms'].values())
    question_marks: str = ','.join(['?'] * num_of_fields)
    insert_query: str = \
        f"""INSERT INTO symptoms (patient_id, {', '.join(
            patient_symptoms['patient_symptoms'].keys()
        )}) VALUES ({question_marks})"""

    cursor.execute(insert_query, (patient_ids[0][0], *symptom_flags))
    conn.commit()
    conn.close()
    return {
        'message': 'Patient symptom data loaded successfully.',
        'patient_id': patient_ids[0]
    }


@api.get('/api/results')
def process_patient_data() -> dict[str, Any]:
    """Process patient data to diagnose diseases based on symptoms and biomarkers."""
    patient_data = api.state.patient_data
    symptoms = api.state.symptoms
    diseases = api.state.diseases
    biomarker_stats_df = api.state.biomarker_stats_df
    biomarker_df = api.state.biomarker_df

    per_disease_stats: dict[str, dict[str, int]] = {}
    all_results: list[dict[str, Any]] = []

    # Process each patient
    for index, patient_row in enumerate(patient_data):
        patient_id = str(patient_row.get(
            'patient_id', f'Patient_{index+1}')).strip()
        true_label = str(patient_row.get('label', '')).strip().lower()
        positive_symptoms = process_patient_symptoms(patient_row=patient_row,
                                                     symptoms=symptoms)
        disease_probabilities = diagnose_patient(diseases=diseases,
                                                 symptoms=symptoms,
                                                 positive_symptoms=positive_symptoms)
        top_disease_symptoms, top_prob_symptoms = disease_probabilities[0]

        # Duplicate dengue/yellow fever to severe/non-severe for downstream layers (NO splitting)
        expanded_disease_probabilities = expand_disease_probabilities(
            disease_probabilities)

        # Get top 1, 2, 3 after symptoms only
        top_symptoms = [None, None, None]
        top_symptoms[0] = top_disease_symptoms.strip().lower() if len(
            expand_disease_probabilities) > 0 else None
        top_symptoms[1] = top_disease_symptoms.strip().lower() if len(
            expanded_disease_probabilities) > 1 else None
        top_symptoms[2] = top_disease_symptoms.strip().lower() if len(
            expanded_disease_probabilities) > 2 else None

        updated_probs = get_updated_probs(biomarker_df=biomarker_df,
                                          patient_id=patient_id,
                                          expanded_disease_probabilities=expanded_disease_probabilities,
                                          biomarker_stats_df=biomarker_stats_df)

        top_disease_biomarkers, top_prob_biomarkers = updated_probs[0]

        # Get top 1, 2, 3 after biomarkers
        top_biomarkers = [None, None, None]
        top_biomarkers[0] = updated_probs[0][0].strip(
        ).lower() if len(updated_probs) > 0 else None
        top_biomarkers[1] = updated_probs[1][0].strip(
        ).lower() if len(updated_probs) > 1 else None
        top_biomarkers[2] = updated_probs[2][0].strip(
        ).lower() if len(updated_probs) > 2 else None

        # Collect per-patient results for later reporting (all outputs needed)
        result = {
            'patient_id': patient_id,
            'true_label': true_label,
            'positive_symptoms': len(positive_symptoms),
            'top1_symptoms': top_symptoms[0],
            'top2_symptoms': top_symptoms[1],
            'top3_symptoms': top_symptoms[2],
            'top1_biomarkers': top_biomarkers[0],
            'top2_biomarkers': top_biomarkers[1],
            'top3_biomarkers': top_biomarkers[2],
            'top_diagnosis_symptoms': top_disease_symptoms,
            'top_probability_symptoms': top_prob_symptoms,
            'top_diagnosis_biomarkers': top_disease_biomarkers,
            'top_probability_biomarkers': top_prob_biomarkers,
            'all_probabilities_symptoms': expanded_disease_probabilities.copy(),
            'all_probabilities_biomarkers': updated_probs.copy()
        }
        all_results.append(result)

        # Count accuracy for each label (disease)
        label = true_label
        if label not in per_disease_stats:
            per_disease_stats[label] = {
                'n': 0,
                'symptoms_top1': 0, 'symptoms_top2': 0, 'symptoms_top3': 0,
                'biomarkers_top1': 0, 'biomarkers_top2': 0, 'biomarkers_top3': 0
            }
        per_disease_stats[label]['n'] += 1
        if label == top_symptoms[0]:
            per_disease_stats[label]['symptoms_top1'] += 1
        if label in [top_symptoms[0], top_symptoms[1]]:
            per_disease_stats[label]['symptoms_top2'] += 1
        if label in [top_symptoms[0], top_symptoms[1], top_symptoms[2]]:
            per_disease_stats[label]['symptoms_top3'] += 1

        if label == top_biomarkers[0]:
            per_disease_stats[label]['biomarkers_top1'] += 1
        if label in [top_biomarkers[0], top_biomarkers[1]]:
            per_disease_stats[label]['biomarkers_top2'] += 1
        if label in [top_biomarkers[0], top_biomarkers[1], top_biomarkers[2]]:
            per_disease_stats[label]['biomarkers_top3'] += 1

    api.state.all_results = all_results
    api.state.per_disease_stats = per_disease_stats

    return {
        'message': 'Patient data processed successfully.',
        'results': all_results,
        'per_disease_stats': per_disease_stats
    }


@api.get('/api/accuracy')
def get_accuracy() -> dict[str, Any]:
    """Calculate and return accuracy statistics for the processed patient data."""
    all_results = api.state.all_results
    per_disease_stats = api.state.per_disease_stats

    if not all_results or not per_disease_stats:
        return {'error': 'No results available. Please process patient data first.'}

    n_patients = len(all_results)
    n_symptoms_top1 = sum(
        1 for r in all_results if r['true_label'] == r['top1_symptoms'])
    n_symptoms_top2 = sum(1 for r in all_results if r['true_label'] in [
        r['top1_symptoms'], r['top2_symptoms']])
    n_symptoms_top3 = sum(1 for r in all_results if r['true_label'] in [
        r['top1_symptoms'], r['top2_symptoms'], r['top3_symptoms']])

    n_biomarkers_top1 = sum(
        1 for r in all_results if r['true_label'] == r['top1_biomarkers'])
    n_biomarkers_top2 = sum(1 for r in all_results if r['true_label'] in [
        r['top1_biomarkers'], r['top2_biomarkers']])
    n_biomarkers_top3 = sum(1 for r in all_results if r['true_label'] in [
        r['top1_biomarkers'], r['top2_biomarkers'], r['top3_biomarkers']])
    return {
        'message': 'Overall and per-disease accuracy calculated successfully.',
        'total_patients': n_patients,
        'symptoms_top1': n_symptoms_top1,
        'symptoms_top2': n_symptoms_top2,
        'symptoms_top3': n_symptoms_top3,
        'biomarkers_top1': n_biomarkers_top1,
        'biomarkers_top2': n_biomarkers_top2,
        'biomarkers_top3': n_biomarkers_top3,
    }


@api.get('/api/accuracy/table')
def generate_accuracy_table() -> dict[str, Any]:
    """Generate a table of accuracy statistics for each disease."""
    per_disease_stats = api.state.per_disease_stats
    if not per_disease_stats:
        return {'error': 'No per-disease statistics available. Please process patient data first.'}
    rows: list[dict[str, Any]] = []
    for disease, stats in sorted(per_disease_stats.items(), key=lambda x: x[0]):
        n = stats['n']
        sym1 = 100 * stats['symptoms_top1'] / n if n else 0
        sym2 = 100 * stats['symptoms_top2'] / n if n else 0
        sym3 = 100 * stats['symptoms_top3'] / n if n else 0
        bio1 = 100 * stats['biomarkers_top1'] / n if n else 0
        bio2 = 100 * stats['biomarkers_top2'] / n if n else 0
        bio3 = 100 * stats['biomarkers_top3'] / n if n else 0
        rows.append({
            'Disease': disease,
            'N_Patients': n,
            'Top1_Symptoms': f'{sym1:.1f}',
            'Top2_Symptoms': f'{sym2:.1f}',
            'Top3_Symptoms': f'{sym3:.1f}',
            'Top1_Biomarkers': f'{bio1:.1f}',
            'Top2_Biomarkers': f'{bio2:.1f}',
            'Top3_Biomarkers': f'{bio3:.1f}',
        })
    return {
        'message': 'Accuracy table generated successfully.',
        'accuracy_table': rows
    }


uvicorn.run(api, host=FAST_API_HOST, port=FAST_API_PORT, log_level='info')
