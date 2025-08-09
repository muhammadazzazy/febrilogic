"""Run the FebriDx multi-page Streamlit application."""
import streamlit as st
from config import FEBRILOGIC_LOGO, UN_SDG_3, UN_SDG_5, UN_SDG_8, UN_SDG_9, UN_SDG_11

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


st.markdown(
    '#### FebriLogic supports the following sustainable development goals of the United Nations:'
)
cols = st.columns(5, gap='small')
cols[0].image(UN_SDG_3, width=225)
cols[1].image(UN_SDG_5, width=225)
cols[2].image(UN_SDG_8, width=225)
cols[3].image(UN_SDG_9, width=225)
cols[4].image(UN_SDG_11, width=225)
