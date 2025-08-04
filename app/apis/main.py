"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
from contextlib import asynccontextmanager
from typing import Any

import uvicorn

from fastapi import FastAPI

from apis.routes import auth, biomarkers, calculate, countries, diseases, patients, symptoms

from apis.config import (
    FAST_API_HOST, FAST_API_PORT
)

from apis.db.database import engine
from apis.db.database import Base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application and set up the database."""
    Base.metadata.create_all(bind=engine)
    yield

api = FastAPI(lifespan=lifespan)

api.include_router(auth.api_router)
api.include_router(biomarkers.api_router)
api.include_router(calculate.api_router)
api.include_router(countries.api_router)
api.include_router(diseases.api_router)
api.include_router(patients.api_router)
api.include_router(symptoms.api_router)


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


if __name__ == '__main__':
    uvicorn.run(api, host=FAST_API_HOST, port=FAST_API_PORT, log_level='info')
