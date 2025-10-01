"""Fetch diseases from the database with caching."""
from functools import lru_cache

from apis.db.database import SessionLocal
from apis.models.model import Disease


@lru_cache(maxsize=1)
def fetch_diseases() -> list[str]:
    """Get diseases stored in the database with caching."""
    with SessionLocal() as db:
        diseases: list[str] = [
            name for (name,) in db.query(Disease.name).all()]
    return diseases
