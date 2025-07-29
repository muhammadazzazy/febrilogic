"""Encapsulate the Patients model for the database."""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from apis.db.database import Base


class Patients(Base):
    """Represent patients table in the database."""
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)
    race = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
