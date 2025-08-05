""""Fetch and return a list of countries from a JSON file."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from apis.db.database import get_db, Session
from apis.models.model import Country
from apis.routes.auth import get_current_user

api_router: APIRouter = APIRouter(
    prefix='/api/countries',
    tags=['countries']
)


@api_router.get('')
def get_countries(user: Annotated[dict, Depends(get_current_user)],
                  db: Session = Depends(get_db)) -> dict[str, list[dict[str, str | int]]]:
    """Fetch countries from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    countries: list[dict[str, str | int]] = [
        {
            'id': country.id,
            'common_name': country.common_name,
            'official_name': country.official_name
        }
        for country in db.query(Country).all()
    ]
    return {
        'countries': countries
    }
