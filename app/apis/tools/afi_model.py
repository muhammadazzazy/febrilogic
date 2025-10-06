"""AFI model for disease diagnosis using symptoms and biomarkers."""
import csv
import math
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.stats import norm

from apis.config import SYMPTOM_WEIGHTS_FILE


def calculate_probabilities(negative_diseases: list[str], positive_symptoms: list[str],
                            biomarker_row: dict[str, float], biomarker_df: DataFrame) -> dict[str, Any]:
    """Calculate disease probabilities based on symptoms and biomarkers."""
    diseases, symptoms = load_disease_data(negative_diseases)

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


def softmax(x: list[float]) -> list[float]:
    """Return list of probabilities from a list of scores using softmax."""
    exp_x = [math.exp(score) for score in x]
    sum_exp_x = sum(exp_x)
    return [exp / sum_exp_x for exp in exp_x]


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


def load_disease_data(negative_diseases: list[str]) \
        -> tuple[dict[str, dict[str, float]], list[str]]:
    """Load disease and symptom data from a CSV file."""
    diseases: dict[str, dict[str, float]] = {}
    symptoms: list[str] = []
    with open(SYMPTOM_WEIGHTS_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            disease_name = row['disease'].strip().title()
            # Skip patient's negative diseases
            if disease_name in negative_diseases:
                continue
            diseases[disease_name] = {}
            if not symptoms:
                symptoms = [col for col in row.keys() if col != 'disease']
            for symptom in symptoms:
                diseases[disease_name][symptom] = float(row[symptom])
    return diseases, symptoms


def expand_diseases_for_severity(disease_probabilities):
    """Expand dengue/yellow fever to severe/non-severe (duplicate their probabilities)."""
    expanded = []
    for d, p in disease_probabilities:
        if d.lower() == "dengue fever":
            expanded.append(("dengue fever severe", p))
            expanded.append(("dengue fever non-severe", p))
        elif d.lower() == "yellow fever":
            expanded.append(("yellow fever severe", p))
            expanded.append(("yellow fever non-severe", p))
        else:
            expanded.append((d, p))
    return expanded


def update_with_all_biomarkers(disease_names, priors, df, biomarker_row):
    """Update probabilities using all available biomarkers."""
    biomarker_names = sorted([
        col.replace('pooled_mean_', '')
        for col in df.columns if col.startswith('pooled_mean_')
    ])
    posteriors = np.array(priors)
    for biomarker in biomarker_names:
        means = df[f'pooled_mean_{biomarker}']
        sds = df[f'pooled_sd_{biomarker}']
        if means.isnull().all() or sds.isnull().all():
            continue
        # Only update if patient provided a value
        if biomarker not in biomarker_row:
            continue
        observed = biomarker_row[biomarker]
        likelihoods = []
        for _, disease in enumerate(disease_names):
            row = df[df['disease'] == disease]
            if row.empty:
                likelihood = 1.0
            else:
                mean = row[f'pooled_mean_{biomarker}'].values[0]
                sd = row[f'pooled_sd_{biomarker}'].values[0]
                if pd.isnull(mean) or pd.isnull(sd) or not np.isfinite(mean) or not np.isfinite(sd) or sd <= 0:
                    likelihood = 1.0
                else:
                    likelihood = norm.pdf(
                        observed, loc=float(mean), scale=float(sd))
                    if not np.isfinite(likelihood) or likelihood <= 0:
                        likelihood = 1e-5
            likelihoods.append(likelihood)
        likelihoods = np.array(likelihoods)
        posteriors *= likelihoods
        s = posteriors.sum()
        if not np.isfinite(s) or s == 0:
            posteriors = np.array(priors)
            break
        posteriors /= s
    return posteriors
