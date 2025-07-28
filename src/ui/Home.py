"""Run the FebriDx multi-page Streamlit application."""
import streamlit as st

st.set_page_config(
    page_title='FebriDx',
    page_icon='🧪',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🧪 FebriDx')


st.warning("""Disclaimer: This application is for educational purposes only
           and should not be used for actual medical diagnosis or treatment.
           Always consult a healthcare professional for medical advice.""",
           icon="⚠️")

st.info("""FebriDx is funded by the Bartlett grant
        and aims to provide a comprehensive diagnostic tool for dengue and other febrile illnesses.
        This application allows users to input patient information, check symptoms,
        and view biomarkers.""",
        icon="ℹ️")
