"""Represents patient biomarker data in the database."""
from sqlalchemy import Column, DateTime, Float, Integer, ForeignKey
from sqlalchemy.sql import func

from db.database import Base


class PatientBiomarker(Base):
    """Represent M:M relationship between Biomarkers and Patients relations."""
    patient_id = Column(Integer, ForeignKey('patients.id'), primary_key=True)
    biomarker_id = Column(Integer, ForeignKey(
        'biomarkers.id'), primary_key=True)
    biomarker_value = Column(Float, nullable=False)
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
