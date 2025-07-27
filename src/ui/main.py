import requests
import streamlit as st
import time


def get_symptoms() -> list[str]:
    """Fetch the list of symptoms from the API."""
    response = requests.get('http://localhost:8000/api/diseases-symptoms')
    if response.status_code != 200:
        st.error('Failed to fetch symptoms from the API.')
        return []
    return [symptom.replace('_', ' ').title() for symptom in response.json().get('symptoms', [])]


def display_symptom_selection() -> None:
    """Display the symptom selection interface."""
    st.header('🩺 Symptom Selection')
    symptoms = get_symptoms()
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


def display_patient_info() -> None:
    """Display the patient information interface."""
    st.header('ℹ️ Patient Information')
    patient_id = st.text_input('Patient ID', key='patient_id', width=300)
    patient_name = st.text_input('Patient Name', key='patient_name', width=300)
    patient_age = st.number_input('Age', min_value=0, max_value=120,
                                  key='patient_age', width=300)
    submit_button = st.button('Submit Patient Info', key='submit_patient_info')


def main() -> None:
    """Run FebriDx Streamlit application."""
    st.set_page_config(
        page_title='FebriDx',
        page_icon='🧪',
        layout='wide',
        initial_sidebar_state='expanded'
    )
    st.title('🧪 FebriDx')
    st.sidebar.title('Dashboard')

    if 'view' not in st.session_state:
        st.session_state.view = 'none'

    if st.sidebar.button('ℹ️ Patient Information'):
        st.session_state.view = 'patient_info'
        st.session_state.loading = True

    if st.sidebar.button('🩺 Symptom Selection'):
        st.session_state.view = 'symptoms'
        st.session_state.loading = True

    content = st.empty()

    if st.session_state.get('loading', False):
        with content.container():
            with st.spinner('Loading...'):
                time.sleep(1.5)
        st.session_state.loading = False

    with content.container():
        if st.session_state.view == 'patient_info':
            display_patient_info()
        elif st.session_state.view == 'symptoms':
            display_symptom_selection()


if __name__ == '__main__':
    main()
