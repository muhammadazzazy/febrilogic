"""Show Patient Information page for FebriLogic."""
import time
from datetime import datetime

import requests
from requests.exceptions import HTTPError

import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT


st.set_page_config(
    page_title='Patient Information',
    page_icon='ℹ️',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('token', '')

st.header('ℹ️ Patient Information')
if 'patient_info' not in st.session_state:
    st.session_state.submitted = False

cols = st.columns(6, gap='medium', border=False)
if cols[-1].button(label='Reset',
                   use_container_width=True,
                   icon='🔄',):
    st.session_state.patient_name = ''
    st.session_state.patient_age = 0
    st.session_state.patient_sex = 'Please Select'
    st.session_state.patient_race = 'Please Select'
    st.rerun()


with st.form('patient_info_form'):
    columns = st.columns(2, gap='medium', border=True)
    date = columns[0].date_input('Date', key='date', value=datetime.today(),
                                 width='stretch')
    patient_name: str = columns[1].text_input(label='Patient Name',
                                              key='patient_name',
                                              width='stretch')
    patient_age: int = columns[0].number_input(label='Age',
                                               min_value=0, max_value=120,
                                               key='patient_age', width='stretch', value=0)
    patient_sex: str = columns[1].selectbox(label='Sex', options=['Please Select', 'Male',
                                                                  'Female', 'Other'],
                                            key='patient_sex', index=0, width='stretch')
    patient_race: str = columns[0].selectbox(label='Race',
                                             options=['Please Select',
                                                      'American Indian or Alaska Native',
                                                      'Asian',
                                                      'Black or African American',
                                                      'Native Hawaiian or Other Pacific Islander',
                                                      'White', 'Other Race', 'Two or More Races'],
                                             key='patient_race', index=0, width='stretch')
    btn_cols = st.columns(6, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        label='Next',
        use_container_width=True,
        icon='➡️'
    )

if submitted:
    missing_fields: list[str] = []
    if patient_sex == 'Please Select':
        missing_fields.append('Sex')
    if patient_race == 'Please Select':
        missing_fields.append('Race')
    if missing_fields:
        st.error(f'Missing fields: {", ".join(missing_fields)}')
        time.sleep(1.5)
        st.stop()
    st.session_state.submitted = True

patient: dict[str, str | int] = {
    'name': str(patient_name),
    'age': int(patient_age),
    'sex': str(patient_sex),
    'race': str(patient_race)
}

if st.session_state.submitted:
    st.session_state.submitted = False
    try:
        with st.spinner('Submitting patient information...', show_time=True):
            response = requests.post(
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                url=f'{FAST_API_BASE_URL}/api/patient',
                json=patient,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()

        st.success('Patient information submitted successfully.', icon='✅')
        time.sleep(1.5)
        st.switch_page('./pages/3_Symptom_Checker.py')
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting patient information: {error_detail}')
        st.stop()
