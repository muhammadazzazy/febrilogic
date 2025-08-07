from typing import Final
import re
import streamlit as st


st.set_page_config(
    page_title='Contact',
    page_icon=':material/contact_mail:',
    layout='wide',
    initial_sidebar_state='expanded'
)

MINIMUM_MESSAGE_LENGTH: Final[int] = 30

st.header('📧 Contact Us')

columns = st.columns(3, gap='small', border=False)
with columns[1].form('contact_form'):
    name = st.text_input('Name', placeholder='Enter your name')
    subject = st.text_input(
        'Subject', placeholder='Enter the subject')
    message = st.text_area('Message', placeholder='Type your message here...')
    button_cols = st.columns(2, gap='large')
    submitted = button_cols[1].form_submit_button(
        'Send ✉️', use_container_width=True)

if submitted:
    missing_fields: list[str] = []
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
        'name': name.strip(),
        'email': email.strip(),
        'message': message.strip()
    }
    st.success("Thanks for reaching out! We'll get back to you soon 🚀")
