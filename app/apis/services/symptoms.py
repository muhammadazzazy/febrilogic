"""Load symptom definitions from the database with caching."""
from collections import defaultdict
from functools import lru_cache

from apis.db.database import SessionLocal
from apis.models.model import Symptom, SymptomCategory


@lru_cache(maxsize=1)
def fetch_symptom_definitions() -> defaultdict[str, list[tuple[str, str]]]:
    """Get symptom definitions grouped by category."""
    with SessionLocal() as db:
        results = (
            db.query(SymptomCategory.name, Symptom.name, Symptom.definition)
              .join(Symptom)
              .all()
        )
    category_symptom_definition: defaultdict[str, list[
        tuple[str, str]]] = defaultdict(list)
    for category, symptom, definition in results:
        category_symptom_definition[category].append((symptom, definition))
    return category_symptom_definition
