"""Run the FebriDx multi-page Streamlit application."""
import streamlit as st

st.set_page_config(
    page_title='FebriDx',
    page_icon='🧪',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🧪 FebriDx')


st.warning("""Disclaimer: This application is for research purposes only
           and should not be used for medical diagnosis or treatment.
           Always consult a healthcare professional for medical advice.""",
           icon="⚠️")

st.info("""FebriDx is funded by a grant from the Bartlett Foundation, The American University in Cairo
        to Professor Dr. Hassan Azzazy and aims to provide a comprehensive tool for differential diagnosis of acute febrile illnesses.""",
        icon="ℹ️")
