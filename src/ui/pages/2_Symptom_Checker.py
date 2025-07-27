"""Show Symptom Checker page for FebriDx."""
import requests
from requests.exceptions import RequestException

import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Symptom Checker',
    page_icon='🩺',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('loaded', False)

if not st.session_state.loaded:
    try:
        with st.spinner('Loading symptoms and definitions...'):
            symptoms_response = requests.get(f'{FAST_API_BASE_URL}/api/diseases-symptoms',
                                             timeout=(FAST_API_CONNECT_TIMEOUT,
                                                      FAST_API_READ_TIMEOUT))
            definitions_response = requests.get(f'{FAST_API_BASE_URL}/api/definitions',
                                                timeout=(FAST_API_CONNECT_TIMEOUT,
                                                         FAST_API_READ_TIMEOUT))
        st.success('Symptoms and definitions loaded successfully!')
        st.session_state.loaded = True
        st.session_state.symptoms_response = symptoms_response
        st.session_state.definitions_response = definitions_response
    except RequestException as e:
        st.error(f'Error fetching symptoms: {e}')
        st.stop()

symptoms: list[str] = [symptom.replace('_', ' ').title()
                       for symptom in st.session_state.symptoms_response.json().get('symptoms', [])]

definitions: dict[str, str] = st.session_state.definitions_response.json().get(
    'definitions', {})

st.header('🩺 Symptom Checker')
if 'symptom_states' not in st.session_state:
    st.session_state.symptom_states = {
        symptom: False for symptom in symptoms}
    st.session_state.submitted = False

cols = st.columns(5)
for i, symptom in enumerate(symptoms):
    col = cols[i % 5]
    st.session_state.symptom_states[symptom] = col.checkbox(
        label=symptom,
        value=st.session_state.symptom_states[symptom],
        key=f'{symptom}',
        help=f"{definitions.get(symptom.replace(' ', '_').lower(), 'No definition available.')}",
    )

col = st.columns(5)[4]
if col.button(label='Submit Symptoms', key='submit_symptoms', use_container_width=True, icon='✅'):
    st.session_state.submitted = True

if st.session_state.submitted:
    selected = [s for s, v in st.session_state.symptom_states.items() if v]
    st.success(
        f'Selected symptoms: {", ".join(selected) if selected else "None"}')
    st.session_state.submitted = False
