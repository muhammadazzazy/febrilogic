""""Fetch and return a list of countries from a JSON file."""
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from apis.routes.auth import get_current_user
from apis.config import COUNTRIES_FILE

api_router: APIRouter = APIRouter(
    prefix='/api/countries',
    tags=['countries']
)


@api_router.get('')
def get_countries(user: Annotated[dict, Depends(get_current_user)]) -> dict[str, Any]:
    """Fetch countries from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    with open(file=COUNTRIES_FILE, mode='r', encoding='utf-8') as f:
        data = json.load(f)
    countries = sorted([
        country['name']['common']
        for country in data
        if 'name' in country and 'common' in country['name']
    ])
    return {
        'countries': countries
    }
