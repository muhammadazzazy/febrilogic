"""Encapsulate Biomarkers model for the database."""
from sqlalchemy import Column, String, Integer, Float, DateTime
from db.database import Base


class Biomarker(Base):
    """Represent Biomarkers model in the database."""
    __tablename__ = 'biomarkers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
