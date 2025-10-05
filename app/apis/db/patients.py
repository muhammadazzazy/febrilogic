"""Get latest lab results for a patient."""
from typing import Any

from sqlalchemy import Numeric, cast, func, select

from apis.models.model import (
    Biomarker, Disease, Symptom,
    patient_biomarkers, patient_negative_diseases, patient_symptoms
)

from sqlalchemy.orm import Session


def get_latest_lab_results(patient_id: int, db: Session) -> dict[str, Any]:
    """Get the latest lab results for a patient."""
    latest_datetime = db.execute(
        select(patient_negative_diseases.c.created_at)
        .where(patient_negative_diseases.c.patient_id == patient_id)
        .order_by(patient_negative_diseases.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    negative_diseases: list[str] = db.query(Disease.name).join(
        patient_negative_diseases).filter(
        patient_negative_diseases.c.patient_id == patient_id,
        patient_negative_diseases.c.created_at == latest_datetime
    ).all()

    latest_datetime = db.execute(
        select(patient_symptoms.c.created_at)
        .where(patient_symptoms.c.patient_id == patient_id)
        .order_by(patient_symptoms.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    symptoms: list[tuple[str]] = db.query(Symptom.name).join(patient_symptoms).filter(
        patient_symptoms.c.patient_id == patient_id,
        patient_symptoms.c.created_at == latest_datetime
    ).all()

    latest_datetime = db.execute(
        select(patient_biomarkers.c.created_at)
        .where(patient_biomarkers.c.patient_id == patient_id)
        .order_by(patient_biomarkers.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    biomarkers: list[tuple[str, float]] = db.query(Biomarker.abbreviation, func.round(cast(
        patient_biomarkers.c.value, Numeric), 2)).join(
        patient_biomarkers).filter(
        patient_biomarkers.c.patient_id == patient_id,
        patient_biomarkers.c.created_at == latest_datetime
    ).all()
    return {
        'negative_diseases': [d[0] for d in negative_diseases],
        'symptoms': [s[0].replace('_', ' ').title() for s in symptoms],
        'biomarkers': {b[0]: b[1] for b in biomarkers}
    }
