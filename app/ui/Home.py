"""Run the FebriDx multi-page Streamlit application."""
import streamlit as st
from config import FEBRILOGIC_LOGO

st.set_page_config(
    page_title='FebriLogic',
    page_icon=FEBRILOGIC_LOGO,
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('FebriLogic')

st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

st.warning("""**Disclaimer**: This application is for research purposes only
           and should not be used for medical diagnosis or treatment.
           Always consult a healthcare professional for medical advice.""",
           icon='⚠️')

st.info("""*FebriLogic is funded by a grant from the Bartlett Foundation,
        [The American University in Cairo](https://www.aucegypt.edu/)
        to [Professor Dr. Hassan Azzazy](https://www.aucegypt.edu/fac/hassan-azzazy)
        and aims to provide a comprehensive tool
        for differential diagnosis of acute febrile illnesses.*""",
        icon='ℹ️')


st.markdown("""### Sustainable Development Goals""")
st.markdown("""
            1. Sustainable cities and communities
            2. Good health and well-being
            3. Industry, innovation and infrastructure
            4. Promote health equity""")
