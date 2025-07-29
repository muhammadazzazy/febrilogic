"""Encapsulate the Users model for the database."""
from sqlalchemy import Column, Integer, String

from apis.db.database import Base


class Users(Base):
    """Represent users table in the database."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
