"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
from io import StringIO
from typing import Any

import csv
import fastapi
import pandas as pd
import uvicorn
from fastapi import File, UploadFile
from pandas import DataFrame

from model.afi import (
    process_patient_symptoms, diagnose_patient,
    expand_disease_probabilities, get_updated_probs
)

api = fastapi.FastAPI()

api.state.diseases = None
api.state.symptoms = None
api.state.biomarker_stats_df = None

api.state.patient_data = None
api.state.biomarker_df = None


api.state.all_results = None
api.state.per_disease_stats = None


@api.post('/api/initialize')
async def initialize(symptom_weights_file: UploadFile = File(...),
                     disease_biomarker_file: UploadFile = File(...)) -> dict[str, Any]:
    """Load symptom weights and biomarker statistics from uploaded CSV files."""
    if symptom_weights_file.content_type != 'text/csv':
        return {'error': 'Symptom weights file must be a CSV.'}

    if disease_biomarker_file.content_type != 'text/csv':
        return {'error': 'Biomarker statistics file must be a CSV.'}

    # Stage 1: Symptom Weights Data Loading
    content = await symptom_weights_file.read()
    decoded = content.decode("utf-8")
    file_sim = StringIO(decoded)
    reader = csv.DictReader(file_sim)

    diseases: dict[str, dict[str, float]] = {}
    symptoms: list[str] = []

    for row in reader:
        disease_name: str = row['disease'].strip()
        diseases[disease_name] = {}
        if not symptoms:
            symptoms = [col for col in row.keys() if col != 'disease']
        for symptom in symptoms:
            diseases[disease_name][symptom] = float(row[symptom])

    api.state.diseases = diseases
    api.state.symptoms = symptoms

    # Stage 2: Disease Biomarker Data Loading
    biomarker_content = await disease_biomarker_file.read()

    biomarker_stats_df: DataFrame = pd.read_csv(
        StringIO(biomarker_content.decode('utf-8')))
    biomarker_stats_df['disease'] = biomarker_stats_df['disease'].astype(
        str).str.strip()

    api.state.biomarker_stats_df = biomarker_stats_df

    if not diseases or not symptoms or biomarker_stats_df.empty:
        return {'error': 'Data loading failed. Please check the input files.'}
    return {'message': 'Data loaded successfully.',
            'diseases': list(diseases.keys()),
            'symptoms': symptoms,
            'biomarker_stats': biomarker_stats_df.to_dict(orient='records')}


@api.post('/api/patient')
async def upload_patient_files(patient_file: UploadFile = File(...),
                               biomarker_file: UploadFile = File(...)) -> dict[str, Any]:
    """Load patient data and biomarkers from uploaded CSV files."""
    if patient_file.content_type != 'text/csv':
        return {'error': 'Patient file must be CSV.'}
    if biomarker_file.content_type != 'text/csv':
        return {'error': 'Biomarker file must be CSV.'}

    content = await patient_file.read()
    decoded = content.decode('utf-8')
    file_sim = StringIO(decoded)
    reader = csv.DictReader(file_sim)
    patient_data: list[dict[str, Any]] = list(reader)
    api.state.patient_data = patient_data

    biomarker_content = await biomarker_file.read()

    biomarker_df: DataFrame = pd.read_csv(
        StringIO(biomarker_content.decode('utf-8')))

    api.state.biomarker_df = biomarker_df

    if not patient_data or biomarker_df.empty:
        return {'error': 'No patient data found.'}
    return {
        'message': 'Patient data loaded successfully.',
        'patient_data': patient_data,
        'biomarker_data': biomarker_df.to_dict(orient='records')
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


uvicorn.run(api)
