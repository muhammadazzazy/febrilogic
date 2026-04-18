"""AFI model for disease diagnosis using symptoms and biomarkers."""
from typing import Any

import csv
import numpy as np
import pandas as pd
from scipy.stats import norm

from apis.config import SYMPTOM_WEIGHTS_FILE


def disease_to_biomarker_row_name(display_name: str) -> str | None:
    """Map symptom-layer disease names to `disease` column in biomarker stats CSV."""
    n = display_name.strip().lower()
    return {
        'dengue fever severe': 'Dengue (severe)',
        'dengue fever non-severe': 'Dengue (non-severe)',
        'dengue fever': 'Dengue (non-severe)',
        'yellow fever severe': 'Yellow fever (severe)',
        'yellow fever non-severe': 'Yellow fever',
        'yellow fever': 'Yellow fever',
        'malaria': 'Malaria',
        'leptospirosis': 'Leptospirosis',
        'typhoid': 'Typhoid',
        'enteric fever': 'Typhoid',
        'viral hepatitis': 'Viral Hepatitis',
        'influenza': 'Influenza',
        'spotted fever group': 'Spotted fever group',
        'spotted fever': 'Spotted fever group',
        'scrub typhus': 'Scrub typhus',
        'chikungunia': 'Chikungunia',
        'chikungunya': 'Chikungunia',
    }.get(n)


def get_biomarker_stats_row(df: pd.DataFrame, bio_key: str) -> pd.Series | None:
    """
    Returns the row from biomarker stats DataFrame matching the given bio_key, 
    or None if not found.
    """
    if bio_key is None or (isinstance(bio_key, str) and not bio_key.strip()):
        return None
    key = str(bio_key).strip()
    row = df[df['disease'].astype(str).str.strip() == key]
    if not row.empty:
        return row.iloc[0]
    kl = key.lower()
    row = df[df['disease'].astype(str).str.strip().str.lower() == kl]
    if not row.empty:
        return row.iloc[0]
    return None


def label_matches(true_label: str, predicted: str) -> bool:
    """Returns True if ground-truth label matches a model disease string (lowercase names)."""
    tl: str = (true_label or '').strip().lower()
    pl: str = (predicted or '').strip().lower()
    if not tl or not pl:
        return False
    if tl == pl:
        return True
    synonym_groups = (
        frozenset({'typhoid', 'enteric fever'}),
        frozenset({'spotted fever group', 'spotted fever'}),
        frozenset({'dengue fever', 'dengue fever severe',
                  'dengue fever non-severe'}),
        frozenset({'yellow fever', 'yellow fever severe',
                  'yellow fever non-severe'}),
    )
    for g in synonym_groups:
        if tl in g and pl in g:
            return True
    return False


def softmax_columns(scores) -> np.ndarray:
    """
    Returns array of same shape with column-wise softmax probabilities.
    Each column sums to 1.
    """
    s: np.ndarray = np.asarray(scores, dtype=float)
    mx: np.ndarray = np.max(s, axis=0, keepdims=True)
    e: np.ndarray = np.exp(s - mx)
    return e / np.sum(e, axis=0, keepdims=True)


def load_mc_symptom_weights(
        csv_path: str,
        negative_diseases: list[str]
) -> tuple[list[str], list[str], dict[str, pd.DataFrame], int]:
    """
    Returns diseases, symptoms, and weights_by_disease dictionary mapping disease to 
    DataFrame of shape (n_iter, n_symptoms).
    """
    diseases: dict[str, list[dict[str, float]]] = {}
    symptoms: list[str] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        symptoms = [c for c in fieldnames if c not in ("disease", "iteration")]
        for row in reader:
            disease_name = row['disease'].strip()
            if disease_name in negative_diseases:
                continue
            if disease_name not in diseases:
                diseases[disease_name] = []
            rec = {s: float(row[s]) for s in symptoms}
            rec['iteration'] = int(float(row['iteration']))
            diseases[disease_name].append(rec)

    disease_names: list[str] = sorted(diseases.keys())
    n_iter: int = len(diseases[disease_names[0]]) if disease_names else 0
    weights_by_disease: dict[str, pd.DataFrame] = {}
    for d in disease_names:
        rows = diseases[d]
        rows.sort(key=lambda r: r['iteration'])
        weights_by_disease[d] = pd.DataFrame(
            [{k: r[k] for k in symptoms} for r in rows])

    return disease_names, symptoms, weights_by_disease, n_iter


def load_legacy_symptom_weights(
    csv_path: str, negative_diseases: list[str],
    n_replicates: int = 500
) -> tuple[list[str], list[str], dict[str, pd.DataFrame], int]:
    """
    Returns diseases, symptoms, and weights_by_disease dictionary mapping disease to 
    DataFrame of shape (n_replicates, n_symptoms) by replicating legacy weights.
    """
    diseases: dict[str, dict[str, float]] = {}
    symptoms: list[str] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        symptoms: list[str] = [c for c in fieldnames if c != "disease"]
        for row in reader:
            disease_name = row['disease'].strip()
            if disease_name in negative_diseases:
                continue
            diseases[disease_name] = {s: float(row[s]) for s in symptoms}
    disease_names: list[str] = sorted(diseases.keys())
    weights_by_disease: dict[str, pd.DataFrame] = {}
    for d in disease_names:
        base = diseases[d]
        mat = np.tile(
            np.array([base[s] for s in symptoms], dtype=float), (n_replicates, 1))
        weights_by_disease[d] = pd.DataFrame(mat, columns=symptoms)
    return disease_names, symptoms, weights_by_disease, n_replicates


def load_symptom_weights_auto(
    csv_path: str, negative_diseases: list[str],
    n_replicates: int = 500
) -> tuple[list[str], list[str], dict[str, pd.DataFrame], int]:
    """
    Returns output of load_mc_symptom_weights if 'iteration' column is present, 
    else load_legacy_symptom_weights.
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
    if 'iteration' in fieldnames:
        return load_mc_symptom_weights(csv_path, negative_diseases)
    return load_legacy_symptom_weights(csv_path, negative_diseases, n_replicates=n_replicates)


def extend_weights_for_patient_symptoms(
    weights_by_disease: dict[str, pd.DataFrame],
    disease_names: list[str],
    symptoms: list[str],
    patient_extra_symptoms: list[str]
) -> tuple[list[str], dict[str, pd.DataFrame]]:
    """
    Add missing symptom columns with weight 0 so patient positives are not ignored
    when the column exists in patient data but not in the weight table.
    """
    all_symptoms: list[str] = sorted(
        set(symptoms) | set(patient_extra_symptoms))
    if set(all_symptoms) == set(symptoms):
        return symptoms, weights_by_disease
    for d in disease_names:
        df = weights_by_disease[d]
        for s in all_symptoms:
            if s not in df.columns:
                df[s] = 0.0
        weights_by_disease[d] = df[[c for c in all_symptoms]]
    return all_symptoms, weights_by_disease


def symptom_raw_scores_mc(
    disease_names: list[str],
    symptoms: list[str],
    weights_by_disease: dict[str, pd.DataFrame],
    positive_symptoms: list[str],
    n_iter: int
) -> np.ndarray:
    """
    Pre-softmax AHP scores: for each MC column, sum of weights over positive symptoms per disease.
    Shape (n_base_diseases, n_iter). Ranking by mean(score) matches majority vote of per-draw argmax
    (softmax is monotone). Mean(softmax(p)) ranking does not — it was collapsing symptom accuracy.
    """
    n_d = len(disease_names)
    scores = np.zeros((n_d, n_iter))
    pos_set = set(positive_symptoms)
    for i, d in enumerate(disease_names):
        wdf = weights_by_disease[d]
        if not pos_set:
            scores[i, :] = 0.0
        else:
            use_cols = [
                c for c in symptoms if c in pos_set and c in wdf.columns]
            if not use_cols:
                scores[i, :] = 0.0
            else:
                scores[i, :] = wdf[use_cols].sum(axis=1).values.astype(float)
    return scores


def symptom_probabilities_mc(
    disease_names: list[str],
    symptoms: list[str], weights_by_disease: dict[str, pd.DataFrame],
    positive_symptoms: list[str], n_iter: int
) -> np.ndarray:
    """Returns array of shape (n_base_diseases, n_iter) with column-wise softmax probabilities."""
    scores = symptom_raw_scores_mc(
        disease_names, symptoms, weights_by_disease, positive_symptoms, n_iter
    )
    return softmax_columns(scores)


def expand_probability_matrix(
    base_names: list[str],
    probs_base: np.ndarray
) -> tuple[list[str], np.ndarray]:
    """Expands base disease probabilities into more granular categories for biomarker updating."""
    n_iter = probs_base.shape[1]
    col_names = []
    col_slices = []
    for i, d in enumerate(base_names):
        dl = d.strip().lower()
        pcol = probs_base[i, :]
        if dl == 'dengue fever':
            col_names.extend(
                ['dengue fever severe', 'dengue fever non-severe'])
            col_slices.append(pcol)
            col_slices.append(pcol.copy())
        elif dl == 'yellow fever':
            col_names.extend(
                ['yellow fever severe', 'yellow fever non-severe'])
            col_slices.append(pcol)
            col_slices.append(pcol.copy())
        else:
            col_names.append(d)
            col_slices.append(pcol)
    probs_exp = np.vstack(col_slices) if col_slices else np.zeros((0, n_iter))
    return col_names, probs_exp


def update_with_all_biomarkers_mc(
    disease_names_expanded: list[str],
    priors_mc: np.ndarray,
    biomarker_stats_df: pd.DataFrame,
    biomarker_row: dict[str, Any]
) -> np.ndarray:
    """Returns updated probabilities after applying all available biomarkers sequentially."""
    biomarker_names = sorted(
        col.replace('pooled_mean_', '')
        for col in biomarker_stats_df.columns
        if col.startswith('pooled_mean_')
    )
    df = biomarker_stats_df
    posteriors = np.array(priors_mc, dtype=float, copy=True)
    n_iter = posteriors.shape[1]

    for biomarker in biomarker_names:
        if posteriors.size == 0:
            break
        means_col = f'pooled_mean_{biomarker}'
        sds_col = f'pooled_sd_{biomarker}'
        if means_col not in df.columns or sds_col not in df.columns:
            continue
        if biomarker not in biomarker_row or str(biomarker_row.get(biomarker, "")).strip() in (
            '',
            'NA',
            'nan',
            'None',
        ):
            continue
        try:
            observed = float(biomarker_row[biomarker])
        except (TypeError, ValueError):
            continue

        likelihood_matrix = np.ones((len(disease_names_expanded), n_iter))
        for i, display_name in enumerate(disease_names_expanded):
            bio_key = disease_to_biomarker_row_name(display_name)
            if bio_key is None:
                bio_key = display_name.strip()
            row = get_biomarker_stats_row(df, bio_key)
            if row is None:
                likelihood_matrix[i, :] = 1.0
                continue
            mean = row[means_col]
            sd = row[sds_col]
            if (
                pd.isna(mean)
                or pd.isna(sd)
                or not np.isfinite(mean)
                or not np.isfinite(sd)
                or sd <= 0
            ):
                likelihood_matrix[i, :] = 1.0
            else:
                lik = norm.pdf(observed, loc=float(mean), scale=float(sd))
                if not np.isfinite(lik) or lik <= 0:
                    lik = 1e-5
                likelihood_matrix[i, :] = lik

        posteriors *= likelihood_matrix
        col_sums = posteriors.sum(axis=0, keepdims=True)
        bad = ~np.isfinite(col_sums) | (col_sums == 0)
        if np.any(bad):
            posteriors = np.array(priors_mc, dtype=float, copy=True)
            break
        posteriors /= col_sums

    return posteriors


def aggregate_mc(probs: np.ndarray) -> tuple[np.ndarray]:
    """
    Returns tuple of arrays (mean, p2_5, p97_5), each of shape (n_diseases,).
    Empty arrays are returned if input is empty.
    """
    if probs.size == 0:
        return np.array([]), np.array([]), np.array([])
    mean: np.ndarray = np.mean(probs, axis=1)
    low: np.ndarray = np.percentile(probs, 2.5, axis=1)
    high: np.ndarray = np.percentile(probs, 97.5, axis=1)
    return mean, low, high


def rank_by_mean(names: list[str], mean_probs: np.ndarray) -> list[tuple[str, float]]:
    """Returns list of (name, probability) sorted from highest to lowest"""
    order = np.argsort(-mean_probs)
    return [(names[i], float(mean_probs[i])) for i in order]


def cohort_accuracy_per_iteration(
        probs: np.ndarray, exp_names: list[str], true_label: str
) -> tuple[np.ndarray]:
    """
    Returns tuple of three arrays (c1, c2, c3), each of shape (n_iter,), containing
    binary indicators (0.0 or 1.0) for top-1, top-2, and top-3 correctness
    per iteration.
    """
    if probs.size == 0:
        return np.array([]), np.array([]), np.array([])
    n_exp, n_iter = probs.shape
    if n_exp == 0:
        return np.zeros(n_iter), np.zeros(n_iter), np.zeros(n_iter)
    _tl = (true_label or '').strip().lower()
    c1 = np.zeros(n_iter)
    c2 = np.zeros(n_iter)
    c3 = np.zeros(n_iter)
    for j in range(n_iter):
        order = np.argsort(-probs[:, j])
        names_j = [exp_names[i].strip().lower() for i in order[:3]]
        while len(names_j) < 3:
            names_j.append('')
        t1, t2, t3 = names_j[0], names_j[1], names_j[2]
        c1[j] = 1.0 if label_matches(true_label, t1) else 0.0
        c2[j] = 1.0 if any(label_matches(true_label, x)
                           for x in (t1, t2)) else 0.0
        c3[j] = 1.0 if any(label_matches(true_label, x)
                           for x in (t1, t2, t3)) else 0.0
    return c1, c2, c3


def fraction_mc_draws_true_in_topk_base(
    probs_base: np.ndarray, disease_names: list[str],
    true_label: str, k: int
) -> float:
    """
    Return the fraction of MC draws where the true label appears in the 
    top-k predictions (based on per-draw softmax probabilities). Unlike mean top-k ranking, 
    this captures how often the true label surfaces across stochastic forward passes.
    """
    if probs_base.size == 0:
        return 0.0
    tl: str = (true_label or '').strip()
    if not tl:
        return 0.0
    n_iter = probs_base.shape[1]
    hits = 0
    for j in range(n_iter):
        order = np.argsort(-probs_base[:, j])
        for i in range(min(k, len(order))):
            name = disease_names[int(order[i])].strip().lower()
            if label_matches(tl, name):
                hits += 1
                break
    return hits / n_iter if n_iter else 0.0


def calculate_mean_confidence_intervals(
        negative_diseases: list[str],
        patient_symptoms: list[str],
        patient_biomarkers: dict[str, float],
        biomarker_stats_df) -> dict[str, Any]:
    """Returns result dictionary containing mean and confidence intervals."""
    disease_names, symptoms, weights_by_disease, n_iter = load_symptom_weights_auto(
        csv_path=SYMPTOM_WEIGHTS_FILE, negative_diseases=negative_diseases)
    biomarker_stats_df['disease'] = biomarker_stats_df['disease'].astype(
        str).str.strip()

    symptoms, weights_by_disease = extend_weights_for_patient_symptoms(
        weights_by_disease, disease_names, symptoms, patient_symptoms
    )
    sum_sym_c1 = np.zeros(n_iter)
    sum_sym_c2 = np.zeros(n_iter)
    sum_sym_c3 = np.zeros(n_iter)
    sum_bio_c1 = np.zeros(n_iter)
    sum_bio_c2 = np.zeros(n_iter)
    sum_bio_c3 = np.zeros(n_iter)

    scores_sym_base = symptom_raw_scores_mc(
        disease_names, symptoms, weights_by_disease, patient_symptoms, n_iter
    )
    probs_sym_base = softmax_columns(scores_sym_base)
    exp_names, probs_sym_exp = expand_probability_matrix(
        disease_names, probs_sym_base)

    mean_s_base, lo_s_base, hi_s_base = aggregate_mc(probs_sym_base)
    mean_s, lo_s, hi_s = mean_s_base, lo_s_base, hi_s_base
    mean_raw_base = np.mean(scores_sym_base, axis=1)
    order_base = np.argsort(-mean_raw_base)
    i_top = int(order_base[0]) if len(order_base) > 0 else 0
    top_disease_symptoms = disease_names[i_top] if disease_names else ""
    top_mean_sym = float(mean_s_base[i_top]) if len(
        mean_s_base) > i_top else float('nan')

    symptoms_top1 = (
        disease_names[order_base[0]].strip().lower() if len(
            order_base) > 0 else None
    )
    symptoms_top2 = (
        disease_names[order_base[1]].strip().lower() if len(
            order_base) > 1 else None
    )
    symptoms_top3 = (
        disease_names[order_base[2]].strip().lower() if len(
            order_base) > 2 else None
    )

    if patient_biomarkers:
        priors_bio = np.array(probs_sym_exp, dtype=float, copy=True)
        probs_bio = update_with_all_biomarkers_mc(
            exp_names, priors_bio, biomarker_stats_df, patient_biomarkers
        )
    else:
        probs_bio = np.array(probs_sym_exp, dtype=float, copy=True)

    s1, s2, s3 = cohort_accuracy_per_iteration(
        probs_sym_base, disease_names, ""
    )
    sym_frac_top1 = fraction_mc_draws_true_in_topk_base(
        probs_sym_base, disease_names, '', 1
    )
    sym_frac_top3 = fraction_mc_draws_true_in_topk_base(
        probs_sym_base, disease_names, '', 3
    )
    b1, b2, b3 = cohort_accuracy_per_iteration(
        probs_bio, exp_names, '')
    sum_sym_c1 += s1
    sum_sym_c2 += s2
    sum_sym_c3 += s3
    sum_bio_c1 += b1
    sum_bio_c2 += b2
    sum_bio_c3 += b3

    mean_b, lo_b, hi_b = aggregate_mc(probs_bio)
    bio_ranked = rank_by_mean(exp_names, mean_b)
    top_disease_biomarkers = bio_ranked[0][0] if bio_ranked else ''
    top_mean_bio = bio_ranked[0][1] if bio_ranked else float('nan')

    order_b = np.argsort(-mean_b)
    biomarkers_top1 = exp_names[order_b[0]].strip(
    ).lower() if len(order_b) > 0 else None
    biomarkers_top2 = exp_names[order_b[1]].strip(
    ).lower() if len(order_b) > 1 else None
    biomarkers_top3 = exp_names[order_b[2]].strip(
    ).lower() if len(order_b) > 2 else None
    result = {
        'positive_symptoms': len(patient_symptoms),
        'symptoms_top1': symptoms_top1,
        'symptoms_top2': symptoms_top2,
        'symptoms_top3': symptoms_top3,
        'biomarkers_top1': biomarkers_top1,
        'biomarkers_top2': biomarkers_top2,
        'biomarkers_top3': biomarkers_top3,
        'top_diagnosis_symptoms': top_disease_symptoms,
        'top_probability_symptoms_mean': top_mean_sym,
        'top_diagnosis_biomarkers': top_disease_biomarkers,
        'top_probability_biomarkers_mean': top_mean_bio,
        'symptom_mc_names_base': list(disease_names),
        'symptom_base_mean': dict(zip(disease_names, mean_s_base)),
        'symptom_base_mean_raw': dict(zip(disease_names, mean_raw_base)),
        'symptom_base_ci_low': dict(zip(disease_names, lo_s_base)),
        'symptom_base_ci_high': dict(zip(disease_names, hi_s_base)),
        'symptom_mc_frac_draws_true_top1': sym_frac_top1,
        'symptom_mc_frac_draws_true_top3': sym_frac_top3,
        'symptom_mc_names_expanded': list(disease_names),
        'symptom_mean': dict(zip(disease_names, mean_s)),
        'symptom_ci_low': dict(zip(disease_names, lo_s)),
        'symptom_ci_high': dict(zip(disease_names, hi_s)),
        'biomarker_mc_names_expanded': list(exp_names),
        'biomarker_mean': dict(zip(exp_names, mean_b)),
        'biomarker_ci_low': dict(zip(exp_names, lo_b)),
        'biomarker_ci_high': dict(zip(exp_names, hi_b)),
    }
    return result
