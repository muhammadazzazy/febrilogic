"""Show Symptom Checker page for FebriDx."""
import requests
import streamlit as st

with st.spinner('Loading symptoms...'):
    response = requests.get('http://localhost:8000/api/diseases-symptoms',
                            timeout=10)
if response.status_code != 200:
    st.error('Failed to fetch symptoms from the API.')

symptoms = [symptom.replace('_', ' ').title()
            for symptom in response.json().get('symptoms', [])]

st.header('🩺 Symptom Checker')
if 'symptom_states' not in st.session_state:
    st.session_state.symptom_states = {
        symptom: False for symptom in symptoms}
    st.session_state.submitted = False

cols = st.columns(5)
for i, symptom in enumerate(symptoms):
    col = cols[i % 5]
    st.session_state.symptom_states[symptom] = col.checkbox(
        label=symptom,
        value=st.session_state.symptom_states[symptom],
        key=f'{symptom}'
    )

col = st.columns(5)[4]
if col.button(label='Submit Symptoms', key='submit_symptoms', use_container_width=True):
    st.session_state.submitted = True

if st.session_state.submitted:
    selected = [s for s, v in st.session_state.symptom_states.items() if v]
    st.success(
        f'Selected symptoms: {", ".join(selected) if selected else "None"}')
    st.session_state.submitted = False
