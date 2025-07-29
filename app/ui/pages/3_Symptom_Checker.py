"""Show Symptom Checker page for FebriLogic."""
import time

import requests
from requests.exceptions import HTTPError, RequestException


import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Symptom Checker',
    page_icon='🩺',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('token', '')

st.session_state.setdefault('loaded', False)

if 'symptom_checker_reset' not in st.session_state:
    st.session_state.symptom_checker_reset = False

if not st.session_state.loaded:
    try:
        with st.spinner('Loading symptoms and definitions...'):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/symptoms/definitions',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        st.session_state.loaded = True
        message = st.empty()
        message.success('Symptoms loaded successfully!')
        time.sleep(1.5)
        message.empty()
        st.session_state.response = response
    except HTTPError as e:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching symptoms: {error_detail}')
        st.stop()
    except RequestException as e:
        st.error(f'Error fetching symptoms: {e}')
        st.stop()

if st.session_state.get('response'):
    symptoms: list[str] = [symptom.replace('_', ' ').title()
                           for symptom in
                           st.session_state.response.json().get('symptom_definitions', {}).keys()]
    st.session_state.symptoms = symptoms
    definitions: dict[str, str] = st.session_state.response.json().get(
        'symptom_definitions', {})
    st.session_state.definitions = definitions

st.header('🩺 Symptom Checker')
if 'symptom_states' not in st.session_state or st.session_state.symptom_checker_reset:
    st.session_state.symptom_states = {
        symptom: False for symptom in symptoms}
    st.session_state.submitted = False
    st.session_state.symptom_checker_reset = True


with st.form('symptom_form'):
    cols = st.columns(5, gap='small')
    for i, symptom in enumerate(symptoms):
        col = cols[i % 5]
        col.checkbox(
            label=symptom,
            key=f'{symptom}_checkbox',
            help=definitions.get(symptom.replace(
                ' ', '_').lower(), 'No definition available.')
        )

    btn_cols = st.columns(5, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        'Next',
        use_container_width=True,
        icon='➡️'
    )

if submitted:
    st.session_state.ready = True
    st.rerun()

symptoms: list[str] = st.session_state.get('symptoms', [])
if st.session_state.get('ready', False) and symptoms:
    st.session_state.ready = False
    patient_symptoms: dict[str, dict[str, bool] | str] = {
        symptom.replace(' ', '_').replace('/', '_').replace('-', '_').lower():
        st.session_state.get(f'{symptom}_checkbox', False)
        for symptom in symptoms
    }
    try:
        st.empty()
        with st.spinner('Submitting symptoms...'):
            response = requests.post(
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                url=f'{FAST_API_BASE_URL}/api/symptoms',
                json=patient_symptoms,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Symptoms submitted successfully.', icon='✅')
        selected = [s.replace('_', ' ').title()
                    for s, v in patient_symptoms.items() if v]
        st.info(f"Selected: {', '.join(selected) if selected else 'None'}")
        time.sleep(1.5)
        st.switch_page('./pages/4_Biomarkers.py')
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting symptoms: {error_detail}')
        st.stop()
