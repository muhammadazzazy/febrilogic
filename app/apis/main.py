"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI

from apis.routes import auth, biomarkers, contact, countries, diseases, patients, symptoms
from apis.config import (
    FAST_API_HOST, FAST_API_PORT
)
from apis.db.database import Base, engine
from apis.services.biomarkers import get_biomarker_stats


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application and set up the database."""
    Base.metadata.create_all(bind=engine)
    get_biomarker_stats()
    yield

api = FastAPI(lifespan=lifespan)

api.include_router(auth.api_router)
api.include_router(biomarkers.api_router)
api.include_router(contact.api_router)
api.include_router(countries.api_router)
api.include_router(diseases.api_router)
api.include_router(patients.api_router)
api.include_router(symptoms.api_router)


if __name__ == '__main__':
    uvicorn.run(api, host=FAST_API_HOST, port=FAST_API_PORT, log_level='info')
