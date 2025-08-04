import time

import requests
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Results',
    page_icon='📊',
    layout='wide',
)

if not st.session_state.get('token', ''):
    st.error('Please log in to access results.')
    st.stop()

st.title('📊 Results')

try:
    response = requests.get(f"{FAST_API_BASE_URL}/api/calculate/{st.session_state.get('patient_id')}",
                            headers={
        'Authorization': f"Bearer {st.session_state.get('token')}"},
        timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
    response.raise_for_status()
    st.write(response.json())
    time.sleep(5)
except requests.exceptions.ConnectionError:
    st.error(
        'Failed to connect to the API. Please check your internet connection or try again later.')
    st.stop()
