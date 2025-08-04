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

st.session_state.setdefault('symptoms_loaded', False)

if not st.session_state.get('token', ''):
    st.error('Please log in to access patient symptoms.')
    st.stop()

st.header('🩺 Symptom Checker')


cols = st.columns(5, gap='large', border=False)

if st.session_state.get('patient_ids'):
    st.session_state.patient_id = int(cols[0].selectbox(
        label='Select a patient',
        key='symptom_checker_selectbox',
        options=st.session_state.get('patient_ids'),
        index=st.session_state.get('patient_id')-1
    ))
else:
    st.error('No patients available. Please add a patient first.')
    st.stop()


def reset_button() -> None:
    """Reset the symptom checkboxes."""
    for symptom_name in symptom_names:
        st.session_state[f'{symptom_name}_checkbox'] = False


cols[4].button(
    label='Reset',
    key='symptom_checker_reset',
    icon='🔄',
    on_click=reset_button,
    use_container_width=True
)

if not st.session_state.get('symptoms_loaded', False):
    try:
        with st.spinner('Loading symptom metadata...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/symptoms/categories-definitions',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        st.session_state.category_symptom_definition = response.json().get(
            'category_symptom_definition', {})
        st.session_state.symptoms_loaded = True
        message = st.empty()
        message.success('Symptoms loaded successfully!')
        time.sleep(1.5)
        message.empty()
    except HTTPError as e:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching symptoms: {error_detail}')
        st.stop()
    except RequestException as e:
        st.error(f'Error fetching symptoms: {e}')
        st.stop()

category_symptom_definition = st.session_state.get(
    'category_symptom_definition', {}
)

with st.container(key='symptom_checker_container', border=True):
    total_cols = st.columns(3, gap='medium', border=False)
    i: int = 0
    for category, symptoms in category_symptom_definition.items():
        with total_cols[i % 3]:
            category_col = st.columns(1, gap='medium', border=True)
            with category_col[0]:
                st.markdown(f'#### {category}')
                for symptom in symptoms:
                    st.checkbox(
                        label=symptom[0].replace('_', ' ').title(),
                        key=f'{symptom[0]}_checkbox',
                        help=symptom[1],
                    )
        i += 1

    btn_cols = st.columns(5, gap='medium')
    submitted = btn_cols[-1].button(
        'Next',
        use_container_width=True,
        icon='➡️'
    )

if submitted:
    st.session_state.ready = True
    st.rerun()


category_symptom_definition = st.session_state.get(
    'category_symptom_definition', {}
)

symptom_names: list[str] = [
    symptom[0] for _, symptoms in category_symptom_definition.items()
    for symptom in symptoms if st.session_state.get(f'{symptom[0]}_checkbox', False)
]

ticked_symptoms: list[str] = []

for symptom in symptom_names:
    if st.session_state.get(f'{symptom}_checkbox', False):
        ticked_symptoms.append(symptom)

if st.session_state.get('ready', False):
    st.session_state.ready = False
    symptom_request: dict[str, dict[str, list[str]]] = {
        'symptom_names': ticked_symptoms
    }
    try:
        st.empty()
        with st.spinner('Submitting patient symptoms...', show_time=True):
            response = requests.post(
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                url=f'{FAST_API_BASE_URL}/api/patients/{st.session_state.patient_id}/symptoms',
                json=symptom_request,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Patient symptoms submitted successfully.', icon='✅')
        time.sleep(1.5)
        st.switch_page('./pages/5_Biomarkers.py')
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting symptoms: {error_detail}')
        st.stop()
