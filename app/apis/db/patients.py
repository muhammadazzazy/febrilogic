"""Get latest lab results for a patient."""
from typing import Any

from sqlalchemy import select

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
    negative_diseases: list[str] = [
        row.name for row in db.query(Disease.name)
        .join(patient_negative_diseases)
        .filter(patient_negative_diseases.c.patient_id == patient_id,
                patient_negative_diseases.c.created_at == latest_datetime).all()
    ]

    latest_datetime = db.execute(
        select(patient_symptoms.c.created_at)
        .where(patient_symptoms.c.patient_id == patient_id)
        .order_by(patient_symptoms.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    positive_symptoms: list[str] = [
        row.name for row in db.query(Symptom.name)
        .join(patient_symptoms)
        .filter(patient_symptoms.c.patient_id == patient_id,
                patient_symptoms.c.created_at == latest_datetime).all()
    ]

    latest_datetime = db.execute(
        select(patient_biomarkers.c.created_at)
        .where(patient_biomarkers.c.patient_id == patient_id)
        .order_by(patient_biomarkers.c.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    biomarker_result: list[tuple[str, float]] = db.query(
        Biomarker.abbreviation,
        patient_biomarkers.c.value
    ).join(
        Biomarker, patient_biomarkers.c.biomarker_id == Biomarker.id).filter(
        patient_biomarkers.c.patient_id == patient_id,
        patient_biomarkers.c.created_at == latest_datetime).all()
    return {
        'negative_diseases': negative_diseases,
        'symptoms': positive_symptoms,
        'biomarkers': biomarker_result
    }
