"""Build LLM prompt based on patient data and disease probabilities."""
from typing import Any

from jinja2 import Template

from apis.config import PROMPT_TEMPLATE
from apis.tools.formatting import format_biomarkers
from apis.models.model import Patient
from apis.services.countries import fetch_countries


def build_prompt(patient: Patient, lab_results: dict[str, Any],
                 disease_probabilities: dict[str, Any]) -> str:
    """Build a prompt for the LLM based on patient data and disease probabilities."""
    country: str = fetch_countries(
    )[patient.country_id - 1]['common_name']
    if patient.race:
        patient: dict[str, int | str] = {
            'age': patient.age,
            'country': country,
            'sex': patient.sex,
            'race': patient.race
        }
    else:
        patient: dict[str, int | str] = {
            'age': patient.age,
            'country': country,
            'sex': patient.sex
        }
    negative_diseases = lab_results.get('negative_diseases', [])
    symptoms = lab_results.get('symptoms', [])
    biomarkers = lab_results.get('biomarkers', {})
    formatted_biomarkers: list[str] = format_biomarkers(biomarkers)
    biomarker_probabilities: list[tuple[str, float]] = disease_probabilities.get(
        'biomarker_probabilities', [])
    top_3_diagnoses: list[tuple[str, float]] = [
        (d[0], d[1]) for d in biomarker_probabilities[:3]
    ]
    template: Template = Template(PROMPT_TEMPLATE.read_text())
    dynamic_data: dict[str, Any] = {
        'patient_info': f"Age {patient['age']}, {patient['country']}, {patient['sex']}, {patient['race']}",
        'negative_diseases': ', '.join(negative_diseases),
        'symptoms': ', '.join(symptoms),
        'biomarkers': '\n'.join(formatted_biomarkers),
        'top_3_diagnoses': top_3_diagnoses
    }
    rendered_prompt: str = template.render(**dynamic_data)
    print(f'Rendered prompt: {rendered_prompt}')
    return rendered_prompt
