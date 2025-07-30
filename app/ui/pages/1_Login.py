"""Show the login page for FebriLogic."""
import time

import requests
from requests.exceptions import HTTPError

import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Login',
    page_icon='🔑',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🔑 Login')

if 'token' in st.session_state:
    del st.session_state['token']

st.session_state.setdefault('token', '')

st.session_state.setdefault('submitted', False)
st.session_state.setdefault('ready', False)

cols = st.columns(3, gap='large', border=False)

with cols[1].form('login_form', clear_on_submit=True, ):
    cols = st.columns(1, gap='large', border=False)
    with cols[0]:
        st.text_input('Username', key='username',
                      placeholder='Enter your username')
    with cols[0]:
        st.text_input('Password', key='password', type='password',
                      placeholder='Enter your password')
    if cols[0].form_submit_button(
        label='Login',
        use_container_width=True,
        icon='🔐'
    ):
        st.session_state.submitted = True

if st.session_state.get('submitted', False):
    st.session_state.submitted = False
    missing_fields: list[str] = []
    if not st.session_state.get('username', '').strip():
        missing_fields.append('Username')
    if not st.session_state.get('password', '').strip():
        missing_fields.append('Password')
    cols = st.columns(3, gap='large', border=False)
    if missing_fields:
        cols[1].error(
            f'Please fill in the following fields: {", ".join(missing_fields)}'
        )
        time.sleep(2)
        st.rerun()
    else:
        st.session_state.ready = True


if st.session_state.ready:
    st.session_state.submitted = False
    st.session_state.ready = False
    cols = st.columns(3, gap='large', border=False)
    try:
        with cols[1]:
            with st.spinner('Logging in...'):
                response = requests.post(f'{FAST_API_BASE_URL}/auth/token',
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT),
                                         data={'username': st.session_state.get('username', ''),
                                               'password': st.session_state.get('password', '')})
                response.raise_for_status()
        cols[1].success('Login successful!')
        time.sleep(1.5)
        st.session_state.token = response.json().get('access_token', '')
        st.session_state.logged_in = True
        st.switch_page('./pages/2_Patient_Information.py')
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        cols[1].error(f"Login unsuccessful: {error_detail}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {e}")
