"""Show Disease Specific Tests page."""
import time

import requests
import streamlit as st

from config import controller, FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT, FEBRILOGIC_LOGO

st.set_page_config(
    page_title='Disease Specific Tests',
    page_icon=':material/lab_panel:',
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
    st.error('Please log in to access the disease-specific tests.')
    st.stop()

if not st.session_state.get('patient_ids', []):
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.error('No patient information available.')
    time.sleep(2)
    st.switch_page('./pages/2_Patient_Information.py')

if st.session_state.get('patient_id') == 0:
    st.error('Please select a patient to proceed.')
    st.stop()

st.title('🧪 Disease-Specific Tests')

st.session_state.setdefault('diseases_loaded', False)

st.markdown(
    '##### Has the patient tested negative using antigen/PCR for any of the following pathogens?'
)
st.markdown('##### *Screening tests are not considered.*')


@st.cache_data(show_spinner=False, ttl=60 * 60)
def fetch_diseases():
    try:
        with st.spinner('Loading disease information...'):
            response = requests.get(url=f'{FAST_API_BASE_URL}/api/diseases',
                                    timeout=(FAST_API_CONNECT_TIMEOUT,
                                             FAST_API_READ_TIMEOUT),
                                    headers={'Authorization': f'Bearer {token}'})
            response.raise_for_status()
        return response.json().get('diseases', [])
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to the API. Please check your connection.")
        st.stop()


if not st.session_state.get('diseases_loaded', False):
    st.session_state.diseases = fetch_diseases()
    st.session_state.diseases_loaded = True

diseases: list[str] = st.session_state.get('diseases', [])

disease_set: set[str] = set()


def reset_button() -> None:
    """Reset the disease specific tests checkboxes."""
    for disease in diseases:
        st.session_state[f'{disease}_checkbox'] = False


patient_id: int = st.session_state.get('patient_id')
index: int = st.session_state.get('patient_ids', []).index(patient_id)
with st.container(border=False):
    cols = st.columns(5)
    cols[0].selectbox(
        label='Select a patient',
        key='disease_specific_tests_selectbox',
        options=st.session_state.get('patient_ids', []),
        index=index
    )
    cols[4].button(
        label='Reset',
        key='disease_specific_tests_reset',
        icon='🔄',
        use_container_width=True,
        on_click=reset_button
    )

with st.form('disease_specific_tests_form'):
    cols = st.columns(2, border=False, gap='small')
    for i, disease in enumerate(diseases):
        cols[i % 2].checkbox(
            label=disease, key=f'{disease}_checkbox')

    cols = st.columns(5)
    submitted = cols[4].form_submit_button(label='Next',
                                           icon='➡️',
                                           use_container_width=True)

checkboxes: dict[str, bool] = {
    disease: st.session_state.get(f'{disease}_checkbox', False)
    for disease in diseases
}

patient_id: int = st.session_state.get('patient_id')
if submitted:
    negative_diseases: list[str] = [disease for disease,
                                    checked in checkboxes.items() if checked]
    try:
        with st.spinner('Submitting negative diseases for selected patient...'):
            response = requests.post(
                url=f'{FAST_API_BASE_URL}/api/patients/{patient_id}/diseases',
                json={
                    'negative_diseases': negative_diseases
                },
                headers={'Authorization': f'Bearer {token}'},
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Negative diseases submitted successfully.')
        time.sleep(2)
        st.switch_page('./pages/5_Symptom_Checker.py')
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        time.sleep(2)
        st.stop()
