"""Show Biomarkers page for FebriLogic."""
import requests
from requests.exceptions import HTTPError
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Biomarkers',
    page_icon='🔬',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('token', '')

st.session_state.setdefault('biomarkers_loaded', False)

if not st.session_state.get('token', ''):
    st.error('Please log in to access patient biomarkers.')
    st.stop()

st.title('🔬 Biomarkers')

if not st.session_state.biomarkers_loaded:
    try:
        with st.spinner('Loading biomarkers and units...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/biomarkers',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
            biomarkers: list[str] = list(
                response.json().get('biomarkers', [])[0].keys())[1:]
            unique_biomarkers: set[str] = set()
            for biomarker in biomarkers:
                biomarker = biomarker.replace('_', ' ').replace(
                    'sd', '').replace('mean', '').replace('pooled', '').strip()
                unique_biomarkers.add(biomarker)
            biomarkers: list[str] = sorted(unique_biomarkers)
            response = requests.get(json=biomarkers,
                                    headers={
                                        'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/biomarkers/units',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
            biomarker_units = response.json().get('biomarker_units', {})
            st.session_state.biomarker_units = biomarker_units
            st.session_state.biomarkers_loaded = True
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching biomarkers: {error_detail}')
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.error('Connection error. Please check your FastAPI server.')
        st.stop()

biomarker_units: dict[str, list[str]
                      ] = st.session_state.get('biomarker_units', {})

with st.form('biomarker_form', clear_on_submit=True):
    cols = st.columns(4, gap='large', border=True)
    reference_values: list[float] = []
    count: int = 0
    for biomarker, units in biomarker_units.items():
        cols[count % 4].number_input(
            label=biomarker,
            min_value=0.0,
            step=0.01,
            format='%.2f',
            width='stretch'
        )
        if not units:
            units = ['No units']
        count += 1
        cols[count % 4].selectbox(
            key=f'{biomarker}_unit',
            label='Units',
            options=units,
            index=0
        )
        count += 1
    btn_cols = st.columns(5, gap='medium')
    submitted = btn_cols[-1].form_submit_button(
        label='Next',
        use_container_width=True,
        icon='➡️'
    )


if submitted:
    st.session_state.submitted = True
