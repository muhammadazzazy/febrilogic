"""Show Disease Specific Tests page."""
import time

import requests
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Disease Specific Tests',
    page_icon=':material/lab_panel:',
)

if not st.session_state.get('token', ''):
    st.error('Please log in to access disease specific tests.')
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.session_state.patient_ids = []
    st.stop()

st.title('🧪 Disease Specific Tests')

st.session_state.setdefault('diseases_loaded', False)

if not st.session_state.get('patient_ids', []):
    st.error('No patients found. Please add a patient first.')
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.stop()

st.markdown(
    '##### Has the selected patient had any disease-specific tests that returned negative results?'
)

if not st.session_state.get('diseases_loaded', False):
    try:
        with st.spinner('Loading disease information...'):
            response = requests.get(url=f'{FAST_API_BASE_URL}/api/diseases',
                                    timeout=(FAST_API_CONNECT_TIMEOUT,
                                             FAST_API_READ_TIMEOUT),
                                    headers={'Authorization': f'Bearer {st.session_state.token}'})
            response.raise_for_status()
        st.session_state.diseases = response.json().get('diseases', [])
        st.session_state.diseases_loaded = True
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to the API. Please check your connection.")
        st.stop()

diseases: list[str] = st.session_state.get('diseases', [])

disease_set: set[str] = set()
for disease in st.session_state.get('diseases', []):
    disease_set.add(disease.replace(
        ' (non-severe)', '').replace(' (severe)', ''))

unique_diseases: list[str] = sorted(disease_set)


def reset_button() -> None:
    """Reset the disease specific tests checkboxes."""
    for unique_disease in unique_diseases:
        st.session_state[f'{unique_disease}_checkbox'] = False


index: int = st.session_state.get(
    'patient_id') - 1 if st.session_state.get('patient_id') else 0

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

with st.container(border=True):
    cols = st.columns(2, border=False, gap='small')
    for i, disease in enumerate(unique_diseases):
        cols[i % 2].checkbox(
            label=disease, key=f'{disease}_checkbox')

    cols = st.columns(5)
    submitted = cols[4].button(label='Next',
                               icon='➡️',
                               use_container_width=True)

checkboxes: dict[str, bool] = {
    disease: st.session_state.get(f'{disease}_checkbox', False)
    for disease in unique_diseases
}
if submitted:
    negative_diseases: list[str] = [disease for disease,
                                    checked in checkboxes.items() if checked]
    if not negative_diseases:
        st.warning('No negative diseases selected. Skipping...')
        time.sleep(2)
        st.switch_page('./pages/4_Symptom_Checker.py')
    try:
        with st.spinner('Submitting negative diseases for selected patient...'):
            response = requests.post(
                url=f'{FAST_API_BASE_URL}/api/patients/{st.session_state.patient_id}/diseases',
                json={
                    'negative_diseases': negative_diseases
                },
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Negative diseases submitted successfully.')
        time.sleep(2)
        st.switch_page('./pages/4_Symptom_Checker.py')
    except requests.exceptions.ConnectionError:
        st.error("Failed to connect to the API. Please check your connection.")
        time.sleep(2)
        st.stop()
