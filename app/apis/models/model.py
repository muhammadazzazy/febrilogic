"""Encapsulate the database models for the FebriLogic backend."""
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from apis.db.database import Base


class User(Base):
    """Represent users table in the database."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    patients: Mapped[List['Patient']] = relationship(back_populates='user')


patient_symptoms = Table(
    'patient_symptoms',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('patient_id', ForeignKey('patients.id')),
    Column('symptom_id', ForeignKey('symptoms.id')),
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


class Symptom(Base):
    """Stores patient symptoms in the database."""
    __tablename__ = 'symptoms'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String, nullable=False)
    definition = Column(String, nullable=False)

    cat_id: Mapped[int] = mapped_column(
        ForeignKey('categories.id'),
        nullable=False
    )

    category: Mapped['Category'] = relationship(
        back_populates='symptoms'
    )


class Category(Base):
    """Store symptom categories in the database."""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    symptoms: Mapped[List[Symptom]] = relationship(back_populates='category')
