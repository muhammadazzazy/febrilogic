"""Fetch countries from the database with caching."""
from functools import lru_cache

from apis.db.database import SessionLocal
from apis.models.model import Country


@lru_cache(maxsize=1)
def get_cached_countries() -> list[dict[str, str | int]]:
    """Fetch countries from the database with caching."""
    with SessionLocal() as db:
        countries: list[dict[str, str | int]] = [
            {
                'id': country.id,
                'common_name': country.common_name,
                'official_name': country.official_name
            }
            for country in db.query(Country).all()
        ]
    return countries
