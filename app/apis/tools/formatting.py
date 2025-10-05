"""Format biomarkers for rendered prompt."""
from decimal import Decimal
from apis.services.biomarkers import fetch_biomarker_units


def format_biomarkers(biomarkers: dict) -> list[str]:
    """Format biomarkers for rendered prompt."""
    formatted_biomarkers: list[str] = []
    for abbreviation, value in biomarkers.items():
        if isinstance(value, Decimal):
            value = int(
                value) if value == value.to_integral() else float(value)
        unit: str = fetch_biomarker_units().get(abbreviation, [''])[0]
        formatted_biomarkers.append(f'- {abbreviation}: {value} {unit}')
    return formatted_biomarkers
