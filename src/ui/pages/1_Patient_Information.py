"""Show Patient Information page for FebriDx."""
from datetime import datetime

import streamlit as st


st.header('ℹ️ Patient Information')
if 'patient_info' not in st.session_state:
    st.session_state.submitted = False
date = st.date_input('Date', key='date', value=datetime.today().isoformat(),
                     width=300)
patient_id = st.text_input('Patient ID', key='patient_id', width=300)
patient_name = st.text_input('Patient Name', key='patient_name', width=300)
patient_age = st.number_input('Age', min_value=0, max_value=120,
                              key='patient_age', width=300)
patient_sex = st.selectbox('Sex', options=['Male', 'Female'],
                           key='patient_sex', index=0, width=300)
race = st.selectbox('Race', options=['White', 'Black', 'Asian', 'Hispanic', 'Other'],
                    key='patient_race', index=0, width=300)
if st.button('Submit Patient Info', key='submit_patient_info'):
    st.session_state.submitted = True
if st.session_state.submitted:
    st.success('Patient information submitted successfully!')
    st.session_state.submitted = False
