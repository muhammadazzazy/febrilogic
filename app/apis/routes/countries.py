""""Fetch and return a list of countries from a JSON file."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apis.services.countries import get_cached_countries
from apis.routes.auth import get_current_user

api_router: APIRouter = APIRouter(
    prefix='/api/countries',
    tags=['countries']
)


@api_router.get('')
def get_countries(
    user: Annotated[dict, Depends(get_current_user)]
) -> dict[str, list[dict[str, str | int]]]:
    """Fetch countries from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed')
    return {
        'countries': get_cached_countries()
    }
