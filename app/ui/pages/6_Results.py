"""Show Results page for FebriLogic."""
import time
from typing import Any

import requests
from requests.exceptions import HTTPError
from pandas import DataFrame
import streamlit as st

from config import controller, FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Results',
    page_icon=':material/bar_chart:',
    layout='wide',
)

if 'token' not in st.session_state:
    token: str = controller.get('token')
    if token:
        st.session_state['token'] = token
else:
    token: str = st.session_state['token']

if token:
    controller.set('token', token)

if not st.session_state.get('patient_ids', []):
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.error('No patients available. Please add a patient first.')
    time.sleep(2)
    st.switch_page('./pages/2_Patient_Information.py')

if st.session_state.get('patient_id') == 0:
    st.error('Please select a patient to proceed.')
    st.stop()

st.title('📊 Results')


patient_id: int = st.session_state.get('patient_id')
index: int = st.session_state.get('patient_ids', []).index(patient_id)

cols = st.columns(5, gap='medium')
patient_id = cols[0].selectbox(label='Select a patient',
                               key='results_selectbox',
                               options=st.session_state.get('patient_ids', []),
                               index=index)

submitted = cols[4].button(label='Submit',
                           icon='📤',
                           use_container_width=True)

if submitted:
    url: str = f'{FAST_API_BASE_URL}/api/patients/{patient_id}/calculate'
    try:
        with st.spinner('Calculating disease probabilities...'):
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': f'Bearer {token}'},
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        symptom_probabilities = response.json().get('symptom_probabilities', [])
        for i, symptom_probability in enumerate(symptom_probabilities):
            symptom_probabilities[i][0] = symptom_probability[0].title()

        biomarker_probabilities = response.json().get(
            'symptom_biomarker_probabilities', [])
        for i, biomarker_probability in enumerate(biomarker_probabilities):
            biomarker_probabilities[i][0] = biomarker_probability[0].title()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()

if submitted:
    symptom_df: DataFrame = DataFrame(symptom_probabilities, columns=[
        'Disease', 'Percentage (%)'])
    symptom_df.sort_values(
        'Percentage (%)', ascending=False, inplace=True)
    symptom_df.index = range(1, len(symptom_df) + 1)
    combined_df: DataFrame = DataFrame(biomarker_probabilities, columns=[
        'Disease', 'Percentage (%)'])
    combined_df: DataFrame = combined_df.sort_values(
        'Percentage (%)', ascending=False)
    combined_df.index = range(1, len(combined_df) + 1)
    with st.expander('Disease probabilities', expanded=True, icon='📈'):
        styled_symptom_df: DataFrame = symptom_df.style.format({"Percentage (%)": "{:.2%}"}).background_gradient(
            subset=['Percentage (%)'], cmap='Reds')
        cols = st.columns(2, gap='medium', border=True)
        cols[0].subheader('After Symptoms')
        cols[0].dataframe(styled_symptom_df, use_container_width=True)
        styled_combined_df: DataFrame = combined_df.style.format({'Percentage (%)': '{:.2%}'}).background_gradient(
            subset=['Percentage (%)'], cmap='Blues')
        cols[1].subheader('After Symptoms + Biomarkers')
        cols[1].dataframe(styled_combined_df, use_container_width=True)

if submitted:
    payload: dict[str, Any] = {
        'symptom_probabilities': symptom_probabilities,
        'biomarker_probabilities': biomarker_probabilities
    }
    headers: dict[str, str] = {
        'Authorization': f'Bearer {token}'
    }
    try:
        with st.spinner('Generating LLM response...'):
            response = requests.post(
                url=f'{FAST_API_BASE_URL}/api/patients/{patient_id}/generate/groq',
                headers=headers,
                json=payload,
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
        response.raise_for_status()
        content: str = response.json().get('content', '')
        with st.expander('LLM Response', expanded=True, icon='🤖'):
            st.write(content)
    except HTTPError as e:
        detail: str = e.response.json().get('detail', 'Unknown error')
        st.error(f'Error generating LLM response: {detail}')
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
