"""Fetch symptom definitions, symptoms, and diseases."""
from collections import defaultdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apis.db.database import get_db
from apis.models.model import SymptomCategory, Symptom
from apis.routes.auth import get_current_user

api_router: APIRouter = APIRouter(
    prefix='/api/symptoms',
    tags=['symptoms']
)


@api_router.get('/categories-definitions')
def get_definitions(user: Annotated[dict, Depends(get_current_user)],
                    db: Session = Depends(get_db)) -> dict[str, Any]:
    """Fetch symptom definitions from the database."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    results = db.query(SymptomCategory.name, Symptom.name,
                       Symptom.definition).join(Symptom).all()
    category_symptom_definition: defaultdict[str,
                                             list[tuple[str, str]]] = defaultdict(list)
    for category_name, symptom_name, definition in results:
        category_symptom_definition[category_name].append(
            (symptom_name, definition))
    return {
        'category_symptom_definition': category_symptom_definition
    }
