"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from apis.routes import auth, biomarkers, contact, countries, diseases, patients, symptoms
from apis.config import (
    FAST_API_HOST, FAST_API_PORT, STREAMLIT_BASE_URL
)
from apis.db.database import Base, engine
from apis.services.biomarkers import fetch_biomarkers, fetch_biomarker_units, get_biomarker_stats
from apis.services.countries import get_cached_countries
from apis.services.diseases import get_diseases
from apis.services.symptoms import get_symptom_definitions


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application and set up the database."""
    Base.metadata.create_all(bind=engine)
    get_biomarker_stats()
    get_diseases()
    get_symptom_definitions()
    get_cached_countries()
    fetch_biomarkers()
    fetch_biomarker_units()
    yield

api = FastAPI(lifespan=lifespan)


@api.get('/')
def index() -> RedirectResponse:
    """Display the home page for the FebriLogic API."""
    return RedirectResponse(url=STREAMLIT_BASE_URL)


api.include_router(auth.api_router)
api.include_router(biomarkers.api_router)
api.include_router(contact.api_router)
api.include_router(countries.api_router)
api.include_router(diseases.api_router)
api.include_router(patients.api_router)
api.include_router(symptoms.api_router)


if __name__ == '__main__':
    uvicorn.run(api, host=FAST_API_HOST, port=FAST_API_PORT, log_level='info')
