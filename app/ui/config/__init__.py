"""Configuration settings for the Streamlit app."""
from pathlib import Path
from typing import Final

import streamlit as st
from streamlit_cookies_controller import CookieController


FAST_API_BASE_URL: Final[str] = st.secrets.get('FAST_API_BASE_URL')

FAST_API_CONNECT_TIMEOUT: Final[int] = st.secrets.get(
    'FAST_API_CONNECT_TIMEOUT', 10)

FAST_API_READ_TIMEOUT: Final[int] = st.secrets.get('FAST_API_READ_TIMEOUT', 30)

FEBRILOGIC_LOGO: Final[str] = Path(__file__).parent.parent / 'assets' / 'febrilogic.png'
print(FEBRILOGIC_LOGO)

controller = CookieController()
