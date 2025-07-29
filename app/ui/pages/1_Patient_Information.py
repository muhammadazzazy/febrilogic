"""Show Patient Information page for FebriDx."""
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

st.header('ℹ️ Patient Information')
if 'patient_info' not in st.session_state:
    st.session_state.submitted = False


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
    patient_sex: str = columns[1].selectbox(label='Sex', options=['Male', 'Female', 'Other'],
                                            key='patient_sex', index=0, width='stretch')
    race: str = columns[0].selectbox(label='Race',
                                     options=['American Indian or Alaska Native',
                                              'Asian',
                                              'Black or African American',
                                              'Native Hawaiian or Other Pacific Islander',
                                              'White', 'Other Race', 'Two or More Races'],
                                     key='patient_race', index=0, width='stretch')
    btn_cols = st.columns(5, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        label='Next',
        use_container_width=True,
        icon='➡️'
    )

if submitted:
    st.session_state.submitted = True

patient: dict[str, str | int] = {
    'name': str(patient_name),
    'age': int(patient_age),
    'sex': str(patient_sex),
    'race': str(race)
}

if st.session_state.submitted:
    st.session_state.submitted = False
    try:
        with st.spinner('Submitting patient information...', show_time=True):
            response = requests.post(
                url=f'{FAST_API_BASE_URL}/api/patient',
                json=patient,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()

        st.success('Patient information submitted successfully.', icon='✅')
        time.sleep(1.5)
        st.switch_page('./pages/2_Symptom_Checker.py')
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting patient information: {error_detail}')
        st.stop()
