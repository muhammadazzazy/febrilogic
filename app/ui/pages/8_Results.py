"""Show Results page for FebriLogic."""
import time
from typing import Any

import requests
import math
import streamlit as st
from requests.exceptions import HTTPError
from pandas import DataFrame

from config import (
    controller,
    FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT,
    FEBRILOGIC_LOGO
)

st.set_page_config(
    page_title='Results',
    page_icon=':material/bar_chart:',
    layout='wide',
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
    st.error('Please log in to access the results.')
    st.stop()

if not st.session_state.get('patient_numbers', []):
    st.session_state.diseases_loaded = False
    st.session_state.diseases = []
    st.error('No patients available. Please add a patient first.')
    time.sleep(2)
    st.switch_page('./pages/4_Patient_Information.py')

if st.session_state.get('patient_number') == 0:
    st.error('Please select a patient to proceed.')
    st.stop()

st.title('📊 Results')


patient_number: int = st.session_state.get('patient_number')
index: int = st.session_state.get('patient_numbers', []).index(patient_number)

cols = st.columns(5, gap='medium')
patient_number = cols[0].selectbox(label='Select a patient',
                                   key='results_selectbox',
                                   options=st.session_state.get(
                                       'patient_numbers', []),
                                   index=index)

submitted = cols[4].button(label='Submit',
                           icon='📤',
                           use_container_width=True)

patient_id = st.session_state.get('patient_id')
if submitted:
    url: str = f'{FAST_API_BASE_URL}/api/patients/{patient_id}/calculate'
    try:
        with st.spinner('Ranking diseases...'):
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': f'Bearer {token}'},
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        results = response.json().get('results', {})

        symptom_mean: dict[str, Any] = results.get('symptom_mean', {})
        symptom_ci_low: dict[str, Any] = results.get('symptom_ci_low', {})
        symptom_ci_high: dict[str, Any] = results.get('symptom_ci_high', {})

        biomarker_mean: dict[str, Any] = results.get('biomarker_mean', {})
        biomarker_ci_low: dict[str, Any] = results.get('biomarker_ci_low', {})
        biomarker_ci_high: dict[str, Any] = results.get(
            'biomarker_ci_high', {})
        biomarker_avg: dict[str, Any] = {}
        biomarker_conf_int_low: dict[str, Any] = {}
        biomarker_conf_int_high: dict[str, Any] = {}
        for key, mean, ci_low, ci_high in zip(
                biomarker_mean.keys(),
                biomarker_mean.values(),
                biomarker_ci_low.values(),
                biomarker_ci_high.values()):
            biomarker_avg[key.title()] = mean
            biomarker_conf_int_low[key.title()] = ci_low
            biomarker_conf_int_high[key.title()] = ci_high

    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()

if submitted:
    symptom_df: DataFrame = DataFrame({
        'Mean': symptom_mean,
        'Confidence Interval (Low)': symptom_ci_low,
        'Confidence Interval (High)': symptom_ci_high
    })
    symptom_df.reset_index(inplace=True)
    symptom_df.rename(columns={'index': 'Disease'}, inplace=True)
    symptom_df.sort_values(
        by='Mean', ascending=False, inplace=True
    )
    symptom_df.index = range(1, len(symptom_df) + 1)
    symptom_df.drop(columns=['Mean', 'Confidence Interval (Low)',
                    'Confidence Interval (High)'], axis=1, inplace=True)

    biomarker_df: DataFrame = DataFrame({
        'Mean': biomarker_avg,
        'Confidence Interval (Low)': biomarker_conf_int_low,
        'Confidence Interval (High)': biomarker_conf_int_high
    })
    biomarker_df.index = biomarker_df.index.str.replace(
        r'(Severe|Non-Severe)$', r'(\1)', regex=True)
    biomarker_df.reset_index(inplace=True)
    biomarker_df.rename(columns={'index': 'Disease'}, inplace=True)
    biomarker_df.sort_values(
        'Mean', ascending=False, inplace=True
    )

    biomarker_df.index = range(1, len(biomarker_df) + 1)
    biomarker_df.drop(
        columns=['Mean', 'Confidence Interval (Low)',
                 'Confidence Interval (High)'], axis=1, inplace=True
    )

    with st.expander('Disease ranking', expanded=True, icon='📈'):
        cols = st.columns(2, gap='medium', border=True)
        cols[0].subheader('After Symptoms')
        cols[0].dataframe(symptom_df, use_container_width=True, )
        cols[1].subheader('After Symptoms + Biomarkers')
        cols[1].dataframe(biomarker_df, use_container_width=True)
