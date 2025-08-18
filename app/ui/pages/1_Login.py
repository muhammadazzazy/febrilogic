"""Show the Login page for FebriLogic."""
import re

import requests
from requests.exceptions import HTTPError
import streamlit as st

from config import controller, FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT, FEBRILOGIC_LOGO

st.set_page_config(
    page_title='Login',
    page_icon=':material/login:',
    layout='wide',
    initial_sidebar_state='expanded'
)
st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

st.title('🔑 Login')

st.session_state.setdefault('login', False)
st.session_state.setdefault('register', False)

st.session_state.token = ''
controller.set('token', st.session_state.token)

cols = st.columns(3, gap='large', border=False)
center_col = cols[1]

with center_col.form('login_form', border=True):
    inner_cols = st.columns(1, gap='large', border=False)
    with inner_cols[0]:
        st.text_input('Email', key='email',
                      placeholder='Enter your email')
    with inner_cols[0]:
        st.text_input('Password', key='password', type='password',
                      placeholder='Enter your password')
    button_cols = st.columns(2, gap='small', border=False)
    st.session_state.login = button_cols[0].form_submit_button(
        label='Login',
        use_container_width=True,
        icon='🔐'
    )
    st.session_state.register = button_cols[1].form_submit_button(
        label='Register',
        use_container_width=True,
        icon='📝'
    )
    button_cols = st.columns(1, gap='small', border=False)
    st.session_state.reset_password = button_cols[0].form_submit_button(
        label='Reset password',
        use_container_width=True,
        icon='🔄'
    )


if st.session_state.get('login', False) or st.session_state.get('register', False):
    st.session_state.login = True
    missing_fields: list[str] = []
    if not st.session_state.get('email', '').strip():
        missing_fields.append('Email')
    if not st.session_state.get('password', '').strip():
        missing_fields.append('Password')
    if missing_fields:
        center_col.error(
            f'Please fill in the following fields: {", ".join(missing_fields)}'
        )
        st.stop()

if st.session_state.get('login', False) or st.session_state.get('register', False) \
        or st.session_state.get('reset', False):
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', st.session_state.get('email', '')):
        center_col.error('Please enter a valid email address.')
        st.stop()


if st.session_state.get('login', False):
    controller.set('token', '')
    st.session_state.login = False
    try:
        with center_col:
            with st.spinner('Logging in...', show_time=True):
                response = requests.post(f'{FAST_API_BASE_URL}/auth/token',
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT),
                                         data={'username': st.session_state.get('email', ''),
                                               'password': st.session_state.get('password', '')})
                response.raise_for_status()
            token = response.json().get('access_token', '')
            st.session_state.token = token
            controller.set('token', token)
        st.switch_page('./pages/2_Patient_Information.py')
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        center_col.error(f"Login unsuccessful: {error_detail}")
        st.stop()
    except requests.exceptions.RequestException as e:
        center_col.error(f'Error connecting to the server: {e}')
        st.stop()

if st.session_state.get('register', False):
    st.session_state.register = False
    try:
        with center_col:
            with st.spinner('Registering...', show_time=True):
                response = requests.post(f'{FAST_API_BASE_URL}/auth',
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT),
                                         json={'email': st.session_state.get('email', ''),
                                               'password': st.session_state.get('password', '')})
                response.raise_for_status()
        center_col.success(
            f"Verification email sent to {st.session_state.get('email', '')}.")
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        center_col.error(f"Registration unsuccessful: {error_detail}")
        st.stop()
    except requests.exceptions.RequestException as e:
        center_col.error(f"Error connecting to the server: {e}")
        st.stop()

if st.session_state.get('reset_password', False):
    payload: dict[str, str] = {
        'email': st.session_state.get('email', '')
    }
    try:
        with center_col:
            with st.spinner('Sending password reset email...', show_time=True):
                response = requests.post(f'{FAST_API_BASE_URL}/auth/reset-password',
                                         json=payload,
                                         timeout=(FAST_API_CONNECT_TIMEOUT,
                                                  FAST_API_READ_TIMEOUT))
                response.raise_for_status()
            center_col.success(
                f"Password reset email sent to {st.session_state.get('email', '')}", icon='✅')
    except requests.exceptions.RequestException as e:
        center_col.error(f'Error connecting to the server: {e}')
        st.stop()
