"""Fetch diseases from the database with caching."""
from functools import lru_cache

from apis.db.database import SessionLocal
from apis.models.model import Disease


@lru_cache(maxsize=1)
def fetch_diseases() -> dict[str, int]:
    """Get diseases stored in the database with caching."""
    with SessionLocal() as db:
        rows = db.query(Disease.id, Disease.name).all()
    return {name: id_ for (id_, name) in rows}
