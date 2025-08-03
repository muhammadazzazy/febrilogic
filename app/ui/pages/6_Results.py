import streamlit as st


st.set_page_config(
    page_title='Results',
    page_icon='📊',
    layout='wide',
)

if not st.session_state.get('token', ''):
    st.error('Please log in to access results.')
    st.stop()

st.title('📊 Results')
