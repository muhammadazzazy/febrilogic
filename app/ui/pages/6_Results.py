"""Show Results page for FebriLogic."""
import requests
from pandas import DataFrame
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Results',
    page_icon=':material/bar_chart:',
    layout='wide',
)

if not st.session_state.get('token', ''):
    st.error('Please log in to access results.')
    st.stop()

st.title('📊 Results')


cols = st.columns(5, gap='medium')
index: int = st.session_state.get(
    'patient_id') - 1 if st.session_state.get('patient_id') else 0
patient_id = cols[0].selectbox(label='Select a patient',
                               key='results_selectbox',
                               options=st.session_state.get('patient_ids', []),
                               index=index)

submitted = cols[4].button(label='Submit',
                           icon='📤',
                           use_container_width=True)

if submitted:
    url: str = f"{FAST_API_BASE_URL}/api/patients/{patient_id}/calculate"
    try:
        with st.spinner('Calculating disease probabilities...'):
            response = requests.get(url=url,
                                    headers={
                                        'Authorization': f"Bearer {st.session_state.get('token')}"},
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
        # st.json(response.json())
        symptom_probabilities = response.json().get('symptom_probabilities', [])
        for i, symptom_probability in enumerate(symptom_probabilities):
            symptom_probabilities[i][0] = symptom_probability[0].title()

        biomarker_probabilities = response.json().get(
            'symptom_biomarker_probabilities', [])
        for i, biomarker_probability in enumerate(biomarker_probabilities):
            biomarker_probabilities[i][0] = biomarker_probability[0].title()

        symptom_df = DataFrame(symptom_probabilities, columns=[
                               'Disease', 'Percentage (%)'])
        symptom_df = symptom_df.sort_values(
            'Percentage (%)', ascending=False)
        with st.expander('Disease probabilities', expanded=True, icon='📈'):
            symptom_df.index = range(1, len(symptom_df) + 1)
            styled_df = symptom_df.style.format({"Percentage (%)": "{:.2%}"}).background_gradient(
                subset=['Percentage (%)'], cmap='Reds')
            cols = st.columns(2, gap='medium')
            cols[0].subheader('After Symptoms Only')
            cols[0].dataframe(styled_df, use_container_width=True)

            combined_df = DataFrame(biomarker_probabilities, columns=[
                'Disease', 'Percentage (%)'])
            combined_df = combined_df.sort_values(
                'Percentage (%)', ascending=False)
            cols[1].subheader('After Symptoms + Biomarkers')
            combined_df.index = range(1, len(combined_df) + 1)
            styled_df = combined_df.style.format({'Percentage (%)': '{:.2%}'}).background_gradient(
                subset=['Percentage (%)'], cmap='Blues')
            cols[1].dataframe(styled_df, use_container_width=True)
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
