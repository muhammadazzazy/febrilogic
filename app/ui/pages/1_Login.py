"""Show the login page for FebriLogic."""
import time

import requests
from requests.exceptions import HTTPError

import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Login',
    page_icon=':material/login:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🔑 Login')

if 'token' in st.session_state:
    st.session_state['token'] = ''

st.session_state.setdefault('token', '')
st.session_state.setdefault('login', False)
st.session_state.setdefault('register', False)

cols = st.columns(3, gap='large', border=False)
with cols[1].form('login_form', clear_on_submit=True, ):
    cols = st.columns(1, gap='large', border=False)
    with cols[0]:
        st.text_input('Email', key='email',
                      placeholder='Enter your email')
    with cols[0]:
        st.text_input('Password', key='password', type='password',
                      placeholder='Enter your password')
    cols = st.columns(2, gap='small', border=False)
    st.session_state.login = cols[0].form_submit_button(
        label='Login',
        use_container_width=True,
        icon='🔐'
    )
    st.session_state.register = cols[1].form_submit_button(
        label='Register',
        use_container_width=True,
        icon='📝'
    )

if st.session_state.get('login', False):
    st.session_state.login = True
    missing_fields: list[str] = []
    if not st.session_state.get('email', '').strip():
        missing_fields.append('Email')
    if not st.session_state.get('password', '').strip():
        missing_fields.append('Password')
    cols = st.columns(3, gap='large', border=False)
    if missing_fields:
        cols[1].error(
            f'Please fill in the following fields: {", ".join(missing_fields)}'
        )
        time.sleep(2)
        st.rerun()

if st.session_state.get('login', False):
    st.session_state.login = False
    cols = st.columns(3, gap='large', border=False)
    try:
        with cols[1]:
            with st.spinner('Logging in...', show_time=True):
                response = requests.post(f'{FAST_API_BASE_URL}/auth/token',
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT),
                                         data={'username': st.session_state.get('email', ''),
                                               'password': st.session_state.get('password', '')})
                response.raise_for_status()
                st.session_state.token = response.json().get('access_token', '')
            cols[1].success('Login successful!')
            time.sleep(2)
        st.switch_page('./pages/2_Patient_Information.py')
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        cols[1].error(f"Login unsuccessful: {error_detail}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {e}")

if st.session_state.get('register', False):
    st.session_state.login = True
    missing_fields: list[str] = []
    if not st.session_state.get('email', '').strip():
        missing_fields.append('Email')
    if not st.session_state.get('password', '').strip():
        missing_fields.append('Password')
    cols = st.columns(3, gap='large', border=False)
    if missing_fields:
        cols[1].error(
            f'Please fill in the following fields: {", ".join(missing_fields)}'
        )
        time.sleep(2)
        st.rerun()

if st.session_state.get('register', False):
    st.session_state.register = False
    cols = st.columns(3, gap='large', border=False)
    try:
        with cols[1]:
            with st.spinner('Registering...', show_time=True):
                response = requests.post(f'{FAST_API_BASE_URL}/auth',
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT),
                                         json={'email': st.session_state.get('email', ''),
                                               'password': st.session_state.get('password', '')})
                response.raise_for_status()
                st.session_state.token = response.json().get('access_token', '')
                response.raise_for_status()
            cols[1].success(response.json().get('message'))
            time.sleep(2)
            st.rerun()
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        cols[1].error(f"Registration unsuccessful: {error_detail}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {e}")
