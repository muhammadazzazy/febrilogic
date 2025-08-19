import requests
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Reset Password',
    page_icon=':material/lock_reset:',
    layout='wide'
)

query_params = st.query_params
token: str | None = query_params.get('token')

if not token:
    st.error('Invalid reset link.')
    st.stop()

st.title('Reset Password')

cols = st.columns(3, gap='small', border=False)

with cols[1].form('reset_password_form'):
    new_password: str = st.text_input('New password', type='password')
    confirm_password: str = st.text_input('Confirm password', type='password')

    submitted: bool = st.form_submit_button(
        'Reset password', icon='🔄')


if submitted and new_password != confirm_password:
    cols[1].error('Passwords do not match.')

if submitted and new_password == confirm_password:
    st.session_state.submitted = False
    try:
        with cols[1]:
            with st.spinner('Resetting password...'):
                response = requests.post(
                    f'{FAST_API_BASE_URL}/auth/reset-password',
                    json={'token': token, 'new_password': new_password},
                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
                )
            response.raise_for_status()
            st.success('Password reset successfully.')
    except requests.RequestException as e:
        st.error(f'Error resetting password: {e}')
