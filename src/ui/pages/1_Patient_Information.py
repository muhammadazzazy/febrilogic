"""Show Patient Information page for FebriDx."""
from datetime import datetime
from typing import Any

import requests
from requests.exceptions import RequestException


import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Patient Information',
    page_icon='ℹ️',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.header('ℹ️ Patient Information')
if 'patient_info' not in st.session_state:
    st.session_state.submitted = False

columns = st.columns(3, gap='medium')
date = columns[0].date_input('Date', key='date', value=datetime.today().isoformat(),
                             width='stretch')
patient_id = columns[1].text_input(
    'Patient ID', key='patient_id', width='stretch')
patient_name = columns[2].text_input(
    'Patient Name', key='patient_name', width='stretch')
patient_age = columns[0].number_input('Age', min_value=0, max_value=120,
                                      key='patient_age', width='stretch')
patient_sex = columns[1].selectbox('Sex', options=['Male', 'Female'],
                                   key='patient_sex', index=0, width='stretch')
race = columns[2].selectbox('Race', options=['White', 'Black', 'Asian', 'Hispanic', 'Other'],
                            key='patient_race', index=0, width='stretch')


patient_data: dict[str, Any] = {
    'date': date.isoformat(),
    'patient_id': str(patient_id),
    'patient_name': str(patient_name),
    'patient_age': int(patient_age),
    'patient_sex': str(patient_sex),
    'patient_race': str(race)
}

if columns[2].button('Submit Patient Information', key='submit_patient_info',
                     icon='✅', use_container_width=True):
    st.session_state.submitted = True
if st.session_state.submitted:
    st.success('Patient information submitted successfully!')
    st.session_state.submitted = False
    try:
        response = requests.post(
            url=f'{FAST_API_BASE_URL}/api/patient',
            json={
                'patient_data': patient_data
            },
            timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
        )
    except RequestException as e:
        st.error(f'Error submitting patient information: {e}')
