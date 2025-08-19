"""Show Symptom Checker page for FebriLogic."""
import time

import requests
import streamlit as st
from requests.exceptions import HTTPError

from config import controller, FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT, FEBRILOGIC_LOGO

st.set_page_config(
    page_title='Symptom Checker',
    page_icon=':material/symptoms:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

st.session_state.setdefault('symptoms_loaded', False)
if 'token' not in st.session_state:
    token: str = controller.get('token')
    if token:
        st.session_state['token'] = token
else:
    token: str = st.session_state['token']

if token:
    controller.set('token', token)
else:
    st.error('Please log in to access the symptom checker.')
    st.stop()

if not st.session_state.get('patient_ids', []):
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.error('No patients available. Please add a patient first.')
    time.sleep(2)
    st.switch_page('./pages/2_Patient_Information.py')

if st.session_state.get('patient_id') == 0:
    st.error('Please select a patient to proceed.')
    st.stop()

st.title('🩺 Symptom Checker')


cols = st.columns(5, gap='large', border=False)


patient_id: int = st.session_state.get('patient_id')
index: int = st.session_state.get('patient_ids', []).index(patient_id)

st.session_state.patient_id = int(cols[0].selectbox(
    label='Select a patient',
    key='symptom_checker_selectbox',
    options=st.session_state.get('patient_ids'),
    index=index
))


@st.cache_data(show_spinner=False, ttl=60 * 60)
def fetch_symptoms():
    try:
        with st.spinner('Loading symptom metadata...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {token}'},
                                    url=f'{FAST_API_BASE_URL}/api/symptoms/categories-definitions',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        time.sleep(1.5)
        return response.json().get(
            'category_symptom_definition', {})
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching symptoms: {error_detail}')
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()


if not st.session_state.get('symptoms_loaded', False):
    st.session_state.category_symptom_definition = fetch_symptoms()
    st.session_state.symptoms_loaded = True


category_symptom_definition = st.session_state.get(
    'category_symptom_definition', {}
)


def reset_button():
    """Reset the symptom checkboxes."""
    for symptoms in category_symptom_definition.values():
        for symptom in symptoms:
            st.session_state[f"{symptom[0]}_checkbox"] = False


cols[4].button(
    label='Reset',
    key='symptom_checker_reset',
    icon='🔄',
    on_click=reset_button,
    use_container_width=True
)

with st.form('symptom_checker_form'):
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
    submitted = btn_cols[-1].form_submit_button(
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


patient_id: int = st.session_state.get('patient_id')
if st.session_state.get('ready', False):
    st.session_state.ready = False
    symptom_request: dict[str, dict[str, list[str]]] = {
        'symptom_names': ticked_symptoms
    }
    try:
        st.empty()
        with st.spinner('Submitting patient symptoms...', show_time=True):
            response = requests.post(
                headers={'Authorization': f'Bearer {token}'},
                url=f'{FAST_API_BASE_URL}/api/patients/{patient_id}/symptoms',
                json=symptom_request,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Patient symptoms submitted successfully.', icon='✅')
        time.sleep(1.5)
        st.switch_page('./pages/6_Biomarkers.py')
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error submitting symptoms: {error_detail}')
        st.stop()
