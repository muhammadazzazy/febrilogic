"""Calculate disease probabilities based on patient symptoms and biomarkers."""
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pandas import DataFrame
from sqlalchemy.orm import Session

from apis.db.database import get_db
from apis.models.model import Symptom, patient_symptoms
from apis.routes.auth import get_current_user
from apis.tools.afi_model import (
    calculate_disease_scores, softmax, load_disease_data, expand_diseases_for_severity,
    print_topk_and_probs, update_with_all_biomarkers
)


from apis.config import BIOMARKER_STATS_FILE, SYMPTOM_WEIGHTS_FILE

api_router: APIRouter = APIRouter(
    prefix='/api/calculate',
    tags=['calculate']
)


@api_router.get('/{patient_id}')
def calculate(patient_id: int, user: Annotated[dict, Depends(get_current_user)],
              db: Session = Depends(get_db)) -> dict[str, Any]:
    """Calculate disease probabilities based on patient symptoms and biomarkers."""
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed.')
    diseases, symptoms = load_disease_data(SYMPTOM_WEIGHTS_FILE)
    biomarker_df: DataFrame = pd.read_csv(BIOMARKER_STATS_FILE)
    biomarker_df['disease'] = biomarker_df['disease'].astype(str).str.strip()
    positive_symptoms: list[str] = db.query(Symptom.name).join(patient_symptoms).filter(
        patient_symptoms.c.patient_id == patient_id
    ).all()
    disease_scores = calculate_disease_scores(diseases=diseases, symptoms=symptoms,
                                              positive_symptoms=positive_symptoms)
    disease_sums = {disease: sum(scores)
                    for disease, scores in disease_scores.items()}
    disease_names = list(disease_sums.keys())
    disease_values = list(disease_sums.values())
    prior_probs = softmax(disease_values)
    sym_probs = list(zip(disease_names, prior_probs))
    sym_probs_expanded = expand_diseases_for_severity(sym_probs)
    sym_probs_expanded = sorted(
        sym_probs_expanded, key=lambda x: x[1], reverse=True)
    print_topk_and_probs("After Symptoms Only", sym_probs_expanded)
    biomarker_row = ask_biomarkers(
        biomarker_df, [d for d, _ in sym_probs_expanded])
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
    print_topk_and_probs("After Symptoms + Biomarkers", bio_probs)
    return {
        'disease_probabilities': bio_probs,
        'disease_scores': disease_scores,
        'symptoms': positive_symptoms
    }
