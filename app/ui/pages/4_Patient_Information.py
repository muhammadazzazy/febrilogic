"""Show Patient Information page for FebriLogic."""
import time
from datetime import datetime
from typing import Any, Final

import requests
import streamlit as st
from requests.exceptions import HTTPError

from config import (
    controller, FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT,
    FAST_API_READ_TIMEOUT, FEBRILOGIC_LOGO
)

st.set_page_config(
    page_title='Patient Information',
    page_icon=':material/info:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

if 'token' not in st.session_state:
    token: str = controller.get('token')
    if token:
        st.session_state['token'] = token
else:
    token: str = st.session_state['token']

if token:
    controller.set('token', token)
else:
    st.error('Please log in to access the patient information.')
    st.stop()

st.title('ℹ️ Patient Information')

cols = st.columns(3, gap='small', border=False)
cols[0].subheader(f"**Date:** {datetime.now().strftime('%d-%m-%Y')}")

st.session_state.setdefault('patients_loaded', False)
st.session_state.setdefault('countries_loaded', False)

if 'patient_info' not in st.session_state:
    st.session_state.submitted = False


@st.cache_data(show_spinner=False, ttl=1)
def get_patient_info() -> list[dict[str, Any]]:
    """Fetch patient information from the FastAPI server."""
    try:
        response = requests.get(
            headers={'Authorization': f'Bearer {token}'},
            url=f'{FAST_API_BASE_URL}/api/patients',
            timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
        )
        response.raise_for_status()
        return response.json().get('patients', [])
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching patient information: {error_detail}')
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()


if not st.session_state.get('patients_loaded', False):
    with st.spinner('Loading patient information...', show_time=True):
        st.session_state.patients = get_patient_info()
        st.session_state.patients_loaded = True


def get_countries() -> list[dict[str, Any]]:
    """Fetch country information from the FastAPI server."""
    try:
        response = requests.get(
            headers={'Authorization': f'Bearer {token}'},
            url=f'{FAST_API_BASE_URL}/api/countries',
            timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
        )
        response.raise_for_status()
        return response.json().get('countries', [])
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error loading country information: {error_detail}')
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your internet connection.')
        st.stop()


if not st.session_state.get('countries_loaded', False):
    with st.spinner('Loading country information...', show_time=True):
        st.session_state.countries = get_countries()
        st.session_state.countries_loaded = True

PLACEHOLDER: Final[str] = 'Please select'

cols = st.columns(6, gap='medium', border=False)

patient_numbers: list[int] = [patient['patient_number']
                              for patient in st.session_state.patients]

st.session_state.patient_numbers = patient_numbers

st.session_state.patient_number = cols[0].selectbox(label='Select a patient',
                                                    key='patient_info_selectbox',
                                                    options=['New patient'] + patient_numbers)

if st.session_state.patient_number == 'New patient':
    st.session_state.patient_number = 0
else:
    st.session_state.patient_id = next(
        (patient['id'] for patient in st.session_state.patients
         if patient['patient_number'] == st.session_state.patient_number), 0)


patients = st.session_state.patients
last_patient_number = st.session_state.get('last_patient_number', None)
if st.session_state.patient_number != last_patient_number:
    st.session_state.last_patient_number = st.session_state.patient_number
    if st.session_state.patient_number == 0:
        st.session_state.patient_age = 0
        st.session_state.patient_country = PLACEHOLDER
        st.session_state.patient_city = ''
        st.session_state.patient_sex = PLACEHOLDER
        st.session_state.patient_race = PLACEHOLDER
    else:
        selected = next(
            (patient for patient in patients
             if patient['patient_number'] == st.session_state.patient_number), None)
        if selected:
            st.session_state.patient_country = st.session_state.countries[selected.get(
                'country_id')-1]['common_name']
            st.session_state.patient_city = selected.get('city', '')
            st.session_state.patient_age = selected['age']
            st.session_state.patient_race = selected.get('race', PLACEHOLDER)
            st.session_state.patient_sex = selected['sex']


if cols[5].button(
    label='Reset',
    use_container_width=True,
    icon='🔄'
):
    st.session_state.patient_age = 0
    st.session_state.patient_sex = PLACEHOLDER
    st.session_state.patient_race = PLACEHOLDER
    st.session_state.patient_country = PLACEHOLDER
    st.session_state.patient_city = ''
    st.session_state.submitted = False

countries = st.session_state.get('countries', [])
common_names: list[str] = sorted(
    [country['common_name'] for country in countries]
)

with st.form('patient_info_form'):
    columns = st.columns(2, gap='medium', border=True)
    patient_age: int = columns[0].number_input(label='Age',
                                               min_value=0, max_value=120,
                                               key='patient_age', width='stretch')
    patient_country: str = columns[1].selectbox(label='Country',
                                                key='patient_country',
                                                options=[
                                                    PLACEHOLDER] + common_names,
                                                width='stretch',
                                                label_visibility='visible')
    patient_sex: str = columns[0].selectbox(label='Sex', options=[PLACEHOLDER, 'Male',
                                                                  'Female', 'Other'],
                                            key='patient_sex', index=0, width='stretch')
    patient_race: str = columns[0].selectbox(label='Race',
                                             options=[PLACEHOLDER,
                                                      'American Indian or Alaska Native',
                                                      'Asian',
                                                      'Black or African American',
                                                      'Native Hawaiian or Other Pacific Islander',
                                                      'White',
                                                      'Middle Eastern or North African',
                                                      'Other Race', 'Two or More Races'],
                                             key='patient_race', index=0, width='stretch')
    patient_city: str = columns[1].text_input(label='City',
                                              key='patient_city',
                                              placeholder='Enter city name',
                                              width='stretch')

    btn_cols = st.columns(6, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        label='Next',
        use_container_width=True,
        icon='➡️'
    )

if submitted:
    missing_fields: list[str] = []
    if patient_country == PLACEHOLDER:
        missing_fields.append('Country')
    if patient_sex == PLACEHOLDER:
        missing_fields.append('Sex')
    if missing_fields:
        st.error(f'Missing fields: {", ".join(missing_fields)}')
        st.stop()
    st.session_state.ready = True


patients: list[dict[str, str | int]] = st.session_state.get('patients', [])

country_id: int = 0
countries = st.session_state.get('countries', [])
for country in countries:
    if country['common_name'] == patient_country:
        country_id = country['id']
        break


def submit_patient_info(url: str, payload: dict[str, Any]) -> None:
    """Submit patient information to the FastAPI server."""
    try:
        with st.spinner('Submitting patient information...', show_time=True):
            response = requests.post(
                url=url,
                headers={'Authorization': f'Bearer {token}'},
                json=payload,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        case_id: int = response.json().get('patient_id')
        return case_id
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting patient information: {error_detail}')
        st.stop()


if st.session_state.get('ready', False):
    st.session_state.ready = False
    st.session_state.patients_loaded = False
    patient_id: int = st.session_state.get('patient_id', 0)
    body: dict[str, str | int] = {
        'age': int(patient_age),
        'city': str(patient_city),
        'country_id': country_id,
        'race': str(patient_race),
        'sex': str(patient_sex)
    }
    route: str = f'{FAST_API_BASE_URL}/api/patients'
    current_patient = next(
        (patient for patient in patients if patient['patient_number'] == st.session_state.patient_number), None)
    if current_patient:
        if int(current_patient['age']) != int(patient_age) \
                or current_patient['city'] != patient_city \
                or current_patient['country_id'] != country_id \
                or current_patient['race'] != patient_race \
                or current_patient['sex'] != patient_sex:
            body['id'] = int(patient_id)
            route += f'/{patient_id}'
        else:
            st.warning('No changes detected in patient information.',
                       icon='⚠️')
            time.sleep(1.5)
            st.switch_page('./pages/5_Disease-Specific_Tests.py')
    else:
        st.session_state.patient_number = len(
            st.session_state.patient_numbers) + 1
    patient_id: int = submit_patient_info(route, body)
    st.session_state.patient_id = patient_id
    if not st.session_state.patient_number in st.session_state.patient_numbers:
        st.session_state.patient_numbers.append(
            st.session_state.patient_number)
    st.success('Patient information submitted successfully.', icon='✅')
    time.sleep(1.5)
    st.switch_page('./pages/5_Disease-Specific_Tests.py')
