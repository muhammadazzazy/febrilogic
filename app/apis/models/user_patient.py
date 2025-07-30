"""Encapsulate the Users model for the database."""
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
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


class Patient(Base):
    """Represent patients table in the database."""
    __tablename__ = 'patients'
    id = mapped_column(Integer, primary_key=True,
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
