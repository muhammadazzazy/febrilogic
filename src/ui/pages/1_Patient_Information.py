"""Show Patient Information page for FebriDx."""
from datetime import datetime

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


with st.form('patient_info_form'):
    columns = st.columns(3, gap='medium')
    date = columns[0].date_input('Date', key='date', value=datetime.today(),
                                 width='stretch')
    patient_id: str = columns[1].text_input(label='Patient ID',
                                            key='patient_id',
                                            width='stretch')
    patient_name: str = columns[2].text_input(label='Patient Name',
                                              key='patient_name',
                                              width='stretch')
    patient_age: int = columns[0].number_input(label='Age',
                                               min_value=0, max_value=120,
                                               key='patient_age',
                                               width='stretch')
    patient_sex: str = columns[1].selectbox(label='Sex', options=['Male', 'Female'],
                                            key='patient_sex', index=0, width='stretch')
    race: str = columns[2].selectbox(label='Race',
                                     options=['White', 'Black',
                                              'Asian', 'Hispanic', 'Other'],
                                     key='patient_race', index=0, width='stretch')
    btn_cols = st.columns(3, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        'Submit Patient Information',
        use_container_width=True,
        icon='✅'
    )

if submitted:
    missing_fields = []
    if not patient_id:
        missing_fields.append('Patient ID')

    if not patient_age:
        missing_fields.append('Patient Age')

    if not patient_sex:
        missing_fields.append('Patient Sex')

    if missing_fields:
        st.error(f'Missing required fields: {", ".join(missing_fields)}')
        st.stop()

    st.session_state.submitted = True

patient_data: dict[str, str | int] = {
    'date': date.isoformat(),
    'patient_id': str(patient_id),
    'name': str(patient_name),
    'age': int(patient_age),
    'sex': str(patient_sex),
    'race': str(race)
}

if st.session_state.submitted:
    st.session_state.submitted = False
    try:
        with st.spinner('Submitting patient information...'):
            response = requests.post(
                url=f'{FAST_API_BASE_URL}/api/patient',
                json={
                    'patient_data': patient_data
                },

                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
        st.success('Patient information submitted successfully.')
    except RequestException as e:
        st.error(f'Error submitting patient information: {e}')
