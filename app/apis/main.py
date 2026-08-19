"""FastAPI application for disease diagnosis using symptoms and biomarkers."""
from contextlib import asynccontextmanager

import uvicorn
import boto3

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from apis.routes import auth, biomarkers, contact, countries, diseases, patients, symptoms
from apis.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME, BIOMARKERS_RANGES_OBJECT, BIOMARKERS_RANGES_PATH,
    FAST_API_HOST, FAST_API_PORT, STREAMLIT_BASE_URL,
    SYMPTOM_WEIGHTS_OBJECT, SYMPTOM_WEIGHTS_PATH
)

from apis.db.database import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application and set up the database."""
    Base.metadata.create_all(bind=engine)

    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3.download_file(BUCKET_NAME, SYMPTOM_WEIGHTS_OBJECT,
                     SYMPTOM_WEIGHTS_PATH)
    s3.download_file(BUCKET_NAME, BIOMARKERS_RANGES_OBJECT,
                     BIOMARKERS_RANGES_PATH)
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
