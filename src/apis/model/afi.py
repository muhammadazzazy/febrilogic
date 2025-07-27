"""AFI model for disease diagnosis using symptoms and biomarkers."""
import math
import numpy as np
import pandas as pd
from numpy import ndarray
from pandas import DataFrame, Series
from scipy.stats import norm


def get_biomarker_row(*, biomarker_df: DataFrame, patient_id: str) -> dict[str, float]:
    """Return biomarker values for a given patient from the biomarker dataframe."""
    # Prepare biomarker values for this patient
    biomarker_row: dict = {}
    if biomarker_df is not None:
        bdf_row = biomarker_df[biomarker_df['patient_id'] == patient_id]
        if not bdf_row.empty:
            biomarker_row = bdf_row.iloc[0].to_dict()
    return biomarker_row


def get_updated_probs(biomarker_df: DataFrame, patient_id: str, expanded_disease_probabilities: list[tuple[str, float]], biomarker_stats_df: DataFrame) -> list[tuple[str, float]]:
    biomarker_row: dict = get_biomarker_row(biomarker_df=biomarker_df,
                                            patient_id=patient_id)

    # Update with all biomarkers if available
    if biomarker_row:
        disease_names = [d for d, _ in expanded_disease_probabilities]
        priors = [p for _, p in expanded_disease_probabilities]
        posteriors = update_with_all_biomarkers(disease_names=disease_names,
                                                priors=priors,
                                                df=biomarker_stats_df,
                                                biomarker_row=biomarker_row)
        updated_probs = list(zip(disease_names, posteriors))
    else:
        updated_probs = expanded_disease_probabilities.copy()

    # Normalize, sort by probability
    total_prob = sum(prob for _, prob in updated_probs)
    if total_prob > 0:
        updated_probs = [(d, p / total_prob) for d, p in updated_probs]
    updated_probs.sort(key=lambda x: x[1], reverse=True)
    return updated_probs


def expand_disease_probabilities(disease_probabilities: list[tuple[str, float]]) \
        -> list[tuple[str, float]]:
    """Expand disease probabilities to include severe/non-severe for dengue/yellow fever."""
    expanded_disease_probabilities = []
    for d, p in disease_probabilities:
        if d.lower() == 'dengue fever':
            expanded_disease_probabilities.append(
                ('dengue fever severe', p))
            expanded_disease_probabilities.append(
                ('dengue fever non-severe', p))
        elif d.lower() == 'yellow fever':
            expanded_disease_probabilities.append(
                ('yellow fever severe', p))
            expanded_disease_probabilities.append(
                ('yellow fever non-severe', p))
        else:
            expanded_disease_probabilities.append((d, p))
    return expanded_disease_probabilities


def softmax(x: list[float]) -> list[float]:
    """Return list of probabilities from a list of scores using softmax."""
    exp_x = [math.exp(score) for score in x]
    sum_exp_x = sum(exp_x)
    return [exp / sum_exp_x for exp in exp_x]


def process_patient_symptoms(*, patient_row: Series, symptoms: list[str]) -> list[str]:
    """Return symptoms that are present in a patient's data."""
    positive_symptoms = []
    for symptom in symptoms:
        if symptom in patient_row:
            value = str(patient_row[symptom]).lower().strip()
            if value in ['yes', 'y', '1', 'true']:
                positive_symptoms.append(symptom)
    return positive_symptoms


def calculate_disease_scores(*, diseases: dict[str, dict[str, float]], symptoms: list[str],
                             positive_symptoms: list[str]) -> dict[str, float]:
    """Return scores for each disease based on positive symptoms."""
    disease_scores = {d: [] for d in diseases}
    for symptom in symptoms:
        for disease_name, disease_data in diseases.items():
            weight = disease_data[symptom]
            if symptom in positive_symptoms:
                disease_scores[disease_name].append(weight)
    return disease_scores


def diagnose_patient(*, diseases: dict[str, dict[str, float]], symptoms: list[str],
                     positive_symptoms: list[str]) -> list[tuple[str, float]]:
    """Diagnose a patient based on their symptoms and disease data."""
    disease_scores = calculate_disease_scores(diseases=diseases,
                                              symptoms=symptoms,
                                              positive_symptoms=positive_symptoms)
    disease_sums = {k: sum(v) for k, v in disease_scores.items()}
    disease_names = list(disease_sums.keys())
    disease_values = list(disease_sums.values())
    probabilities = softmax(disease_values)
    disease_probabilities = list(zip(disease_names, probabilities))
    disease_probabilities.sort(key=lambda x: x[1], reverse=True)
    # No longer returns disease sums
    return disease_probabilities


def compute_likelihoods(*, biomarker: str, disease_names: list[str],
                        df: DataFrame, biomarker_row: Series) -> ndarray:
    """Compute likelihoods for a biomarker given disease names and dataframe."""
    likelihoods = []
    observed = float(biomarker_row[biomarker])
    # For each disease, compute likelihood under normal distribution
    for disease in disease_names:
        row = df[df['disease'] == disease]
        if row.empty:
            likelihood = 1.0  # If disease is missing, use uninformative likelihood
        else:
            mean = row[f'pooled_mean_{biomarker}'].values[0]
            sd = row[f'pooled_sd_{biomarker}'].values[0]
            # Skip if mean/sd are missing/bad
            if pd.isnull(mean) or pd.isnull(sd) or not np.isfinite(mean) \
                    or not np.isfinite(sd) or sd <= 0:
                likelihood = 1.0
            else:
                likelihood = norm.pdf(
                    observed, loc=float(mean), scale=float(sd))
                if not np.isfinite(likelihood) or likelihood <= 0:
                    likelihood = 1e-5  # Avoid zero/neg/NaN likelihoods
        likelihoods.append(likelihood)
    likelihoods = np.array(likelihoods)
    likelihoods[~np.isfinite(likelihoods)] = 1.0
    return likelihoods


def update_with_all_biomarkers(*, disease_names: list[str], priors: list[float],
                               df: DataFrame, biomarker_row: Series) -> ndarray:
    """Update disease probabilities using all biomarkers from the dataframe."""
    # Get all biomarker names from dataframe columns (strip prefix)
    biomarker_names = sorted([
        col.replace('pooled_mean_', '')
        for col in df.columns if col.startswith('pooled_mean_')
    ])
    posteriors = np.array(priors)
    for biomarker in biomarker_names:
        means = df[f'pooled_mean_{biomarker}']
        sds = df[f'pooled_sd_{biomarker}']
        # Skip if means/SDs missing for this biomarker
        if means.isnull().all() or sds.isnull().all():
            continue
        # Only update if patient's biomarker value is present
        if biomarker not in biomarker_row \
                or str(biomarker_row[biomarker]).strip() in ['', 'NA', 'nan', 'None']:
            continue
        likelihoods = compute_likelihoods(biomarker=biomarker, disease_names=disease_names,
                                          df=df, biomarker_row=biomarker_row)
        posteriors *= likelihoods
        s = posteriors.sum()
        if not np.isfinite(s) or s == 0:
            posteriors = np.array(priors)
            break
        posteriors /= s
    return posteriors
