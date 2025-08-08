"""Show Contact Us page for FebriLogic."""
import time
from typing import Final

import requests
import streamlit as st
from requests.exceptions import HTTPError

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Contact',
    page_icon=':material/contact_mail:',
    layout='wide',
    initial_sidebar_state='expanded'
)

MINIMUM_MESSAGE_LENGTH: Final[int] = 10

st.header('📧 Contact Us')

columns = st.columns(3, gap='small', border=False)
with columns[1].form('contact_form'):
    email = st.text_input('Email', placeholder='Enter your email')
    name = st.text_input('Name', placeholder='Enter your name')
    subject = st.text_input(
        'Subject', placeholder='Enter the subject')
    message = st.text_area('Message', placeholder='Type your message here...')
    button_cols = st.columns(2, gap='large')
    submitted = button_cols[1].form_submit_button(
        'Send', use_container_width=True, icon=':material/send:')

if submitted:
    missing_fields: list[str] = []
    if not email.strip():
        missing_fields.append('Email')
    if not name.strip():
        missing_fields.append('Name')
    if not message.strip():
        missing_fields.append('Message')
    if not subject.strip():
        missing_fields.append('Subject')
    if missing_fields:
        st.error(f'Missing fields: {", ".join(missing_fields)}')
        st.stop()

if submitted:
    if len(message.strip()) < MINIMUM_MESSAGE_LENGTH:
        st.error(
            f'Message must be at least {MINIMUM_MESSAGE_LENGTH} characters long.'
        )
        st.stop()

if submitted:
    payload: dict[str, str] = {
        'email': email.strip(),
        'message': message.strip(),
        'name': name.strip(),
        'subject': subject.strip(),
    }
    try:
        with columns[1]:
            with st.spinner('Sending your message...'):
                response = requests.post(
                    f'{FAST_API_BASE_URL}/api/contact',
                    json=payload,
                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT),
                    headers={
                        'Authorization': f'Bearer {st.session_state.get("token", "")}',
                    }
                )
                response.raise_for_status()

        columns[1].success(
            "Thanks for reaching out! We'll get back to you soon", icon=':material/check_circle:')
        time.sleep(2)
    except HTTPError:
        detail: str = response.json().get('detail', 'Unknown error occurred.')
        st.error(f'Error sending message: {detail}')
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
