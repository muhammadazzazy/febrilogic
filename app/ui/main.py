import streamlit as st
from st_pages import get_nav_from_toml, hide_pages

st.set_page_config(
    page_title='FebriLogic',
    layout='wide',
    initial_sidebar_state='expanded'
)

nav = get_nav_from_toml()

pg = st.navigation(nav)

pg.run()
