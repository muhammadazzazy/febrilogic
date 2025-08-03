"""Show Biomarkers page for FebriLogic."""
import time

import requests
from requests.exceptions import HTTPError
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Biomarkers',
    page_icon='🔬',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('token', '')

st.session_state.setdefault('biomarkers_loaded', False)

if not st.session_state.get('token', ''):
    st.error('Please log in to access patient biomarkers.')
    st.stop()

st.title('🔬 Biomarkers')

if not st.session_state.get('patient_ids'):
    st.error('No patients available. Please add a patient first.')
    st.stop()


if not st.session_state.biomarkers_loaded:
    try:
        with st.spinner('Loading biomarker metadata...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/biomarkers',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
            biomarkers: list[dict[str, str]
                             ] = response.json().get('biomarkers', [])
            st.session_state.biomarkers = biomarkers
            st.session_state.biomarkers_loaded = True
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching biomarkers: {error_detail}')
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()

checkboxes: dict[str, bool] = {}

biomarkers: list[dict[str, str]] = st.session_state.get('biomarkers', [])
biomarker_units: dict[str, str] = {
    biomarker['abbreviation']: biomarker['unit'] for biomarker in biomarkers
}

cols = st.columns(5, gap='large', border=False)

cols[0].selectbox(label='Select patient',
                  key='patient_id',
                  options=st.session_state.get('patient_ids'))

biomarker_reference_ranges: dict[str, str] = {
    biomarker['abbreviation']:
    biomarker['reference_range'] + ' ' +
    f'({biomarker_units[biomarker['abbreviation']]})'
    for biomarker in biomarkers
}

count: int = 0
for biomarker, unit in biomarker_units.items():
    with st.container():
        row = st.columns([2, 3, 4], gap='medium', border=False)
        checkboxes[f'{biomarker}'] = row[0].checkbox(
            label=biomarker,
            key=f'{biomarker}_checkbox',
            value=False,
            help=f"{biomarkers[count]['name']}"
        )
        row[0].caption(
            f"Reference Range: {biomarker_reference_ranges[biomarker]}")
    if checkboxes[f'{biomarker}']:
        row[1].number_input(
            label='',
            key=f'{biomarker}_value',
            min_value=0.0,
            step=0.01,
            format='%.2f',
            width='stretch'
        )
        row[2].selectbox(
            key=f'{biomarker}_unit',
            label='',
            options=[unit],
            index=0
        )
    count += 1

btn_cols = st.columns(5, gap='medium')
submitted = btn_cols[-1].button(
    label='Next',
    use_container_width=True,
    icon='➡️'
)


biomarker_values: dict[str, float] = {}
for biomarker, flag in checkboxes.items():
    if flag:
        biomarker_values[biomarker] = st.session_state.get(
            f'{biomarker}_value', 0.0)

if submitted:
    try:
        with st.spinner('Submitting biomarkers...', show_time=True):
            patient_biomarkers_request = {
                'patient_id': st.session_state.get('patient_id'),
                'biomarker_values': biomarker_values
            }
            time.sleep(5)
            response = requests.post(
                json=patient_biomarkers_request,
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                url=f'{FAST_API_BASE_URL}/api/biomarkers',
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Patient biomarkers submitted successfully!')
        time.sleep(2)
        st.session_state.biomarkers_loaded = False
        st.switch_page('./pages/6_Results.py')
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()
