"""Shows the home page."""
import streamlit as st

from config import (
    FEBRILOGIC_LOGO,
    UN_SDG_3, UN_SDG_5, UN_SDG_8, UN_SDG_9, UN_SDG_11,
    STREAMLIT_BASE_URL
)

st.set_page_config(
    page_icon='assets/febrilogic.png',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title(':blue[FebriLogic]')

st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

if 'cookies_accepted' not in st.session_state:
    st.session_state.cookies_accepted = None


@st.dialog('Cookies 🍪')
def consent_cookie() -> None:
    """Show cookie consent dialog."""
    st.markdown(f"""We use cookies to improve your experience on our site,
                so you don't login every time you come back to the app. Please see our [Privacy Policy]({STREAMLIT_BASE_URL}/privacy-policy).""")
    c1, c2 = st.columns(2, gap='small')
    if c1.button('Accept Cookies', use_container_width=True, type='primary'):
        st.session_state.cookies_accepted = True
        st.rerun()
    if c2.button('Decline Cookies', use_container_width=True, type='secondary'):
        st.session_state.cookies_accepted = False
        st.rerun()


if st.session_state.cookies_accepted is None:
    consent_cookie()

if st.session_state.cookies_accepted:
    st.markdown("""#### FebriLogic is an automated tool based on a novel algorithm that leverages real-world data to assist healthcare professionals in the differential diagnosis of acute febrile illnesses (AFIs). In addition to diagnostic assistance, FebriLogic harnesses the power of AI to provide recommendations for further testing and clinical management procedures. FebriLogic suggests the 3 most probable diagnoses from a list of 10 of the most prevalent AFIs.""")

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
    st.warning("""**Disclaimer**: This application is for research purposes only
           and should not be used for medical diagnosis or treatment.
           Always consult a healthcare professional for medical advice.""",
               icon='⚠️')
