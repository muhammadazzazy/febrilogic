"""Encapsulate the database models for the FebriLogic backend."""
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from apis.db.database import Base


class Biomarker(Base):
    """Store biomarker information in the database."""
    __tablename__ = 'biomarkers'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    abbreviation = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True, unique=True)
    standard_unit = Column(String, nullable=False, index=True)
    reference_range = Column(String, nullable=False)


class Country(Base):
    """Store country information in the database."""
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    common_name = Column(String, nullable=False, unique=True)
    official_name = Column(String, nullable=False, unique=True)
    patients: Mapped[List['Patient']] = relationship(back_populates='country')


class Disease(Base):
    """Store disease information in the database."""
    __tablename__ = 'diseases'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False, unique=True)


patient_symptoms = Table(
    'patient_symptoms',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('patient_id', ForeignKey('patients.id'), nullable=False),
    Column('symptom_id', ForeignKey('symptoms.id'), nullable=True),
    Column('created_at', DateTime(timezone=True),
           server_default=func.now())
)


class Patient(Base):
    """Represent patients table in the database."""
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    index=True, autoincrement=True)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=True)
    country = Column(String, nullable=False)
    sex = Column(String, nullable=False)
    race = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now())
    country_id: Mapped[int] = mapped_column(
        ForeignKey('countries.id'),
        nullable=False
    )
    country: Mapped['Country'] = relationship(
        back_populates='patients'
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    user: Mapped['User'] = relationship(
        back_populates='patients'
    )
    symptoms: Mapped[List['Symptom']] = relationship(
        secondary=patient_symptoms,
    )


patient_biomarkers = Table(
    'patient_biomarkers',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('patient_id', ForeignKey('patients.id'), nullable=False),
    Column('biomarker_id', ForeignKey('biomarkers.id'), nullable=True),
    Column('value', Float, nullable=True),
    Column('created_at', DateTime(timezone=True),
           server_default=func.now())
)


patient_negative_diseases = Table(
    'patient_negative_diseases',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('patient_id', ForeignKey('patients.id'), nullable=False),
    Column('disease_id', ForeignKey('diseases.id'), nullable=True),
    Column('created_at', DateTime(timezone=True),
           server_default=func.now())
)


class Symptom(Base):
    """Stores patient symptoms in the database."""
    __tablename__ = 'symptoms'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String, nullable=False, unique=True)
    definition = Column(String, nullable=False)

    cat_id: Mapped[int] = mapped_column(
        ForeignKey('symptom_categories.id'),
        nullable=False
    )

    category: Mapped['SymptomCategory'] = relationship(
        back_populates='symptoms'
    )


class SymptomCategory(Base):
    """Store symptom categories in the database."""
    __tablename__ = 'symptom_categories'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    symptoms: Mapped[List[Symptom]] = relationship(
        back_populates='category'
    )


class User(Base):
    """Represent users table in the database."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True,
                autoincrement=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now())
    hashed_password = Column(String, nullable=False)
    patients: Mapped[List['Patient']] = relationship(back_populates='user')


class Unit(Base):
    """Store unit information in the database."""
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    symbol = Column(String, nullable=False, unique=True, index=True)


biomarker_units = Table(
    'biomarker_units',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('biomarker_id', ForeignKey('biomarkers.id'), nullable=False),
    Column('unit_id', ForeignKey('units.id'), nullable=False),
    Column('factor', Float, nullable=False, default=1.0)
)
