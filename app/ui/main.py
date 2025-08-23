from pathlib import Path
from typing import Final

import streamlit as st
from st_pages import get_nav_from_toml

st.set_page_config(
    page_title='FebriLogic',
    page_icon='assets/febrilogic.png',
    layout='wide',
    initial_sidebar_state='expanded',
)

BASE_DIR: Final[Path] = Path(__file__).parent
PAGES_PATH: Final[Path] = BASE_DIR / '.streamlit' / 'pages.toml'

nav = get_nav_from_toml(PAGES_PATH)

pg = st.navigation(nav)

pg.run()
