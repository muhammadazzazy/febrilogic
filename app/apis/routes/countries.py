""""Fetch and return a list of countries from a JSON file."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apis.services.countries import fetch_countries
from apis.routes.auth import get_current_user

api_router: APIRouter = APIRouter(
    prefix='/api/countries',
    tags=['countries']
)


@api_router.get('')
def get_countries(
    user: Annotated[dict, Depends(get_current_user)],
    countries: Annotated[list[dict[str, str | int]], Depends(fetch_countries)]
) -> dict[str, list[dict[str, str | int]]]:
    """Fetch countries from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'countries': countries
    }
