import streamlit as st
from st_pages import get_nav_from_toml

from config import FEBRILOGIC_LOGO, PAGES_TOML

st.set_page_config(
    page_title='FebriLogic',
    page_icon=FEBRILOGIC_LOGO,
    layout='wide',
    initial_sidebar_state='expanded',
)

nav = get_nav_from_toml(PAGES_TOML)

pg = st.navigation(nav)

pg.run()
