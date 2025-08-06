"""Show Biomarkers page for FebriLogic."""
import time

import requests
from requests.exceptions import HTTPError
import streamlit as st

from config import FAST_API_BASE_URL, FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT

st.set_page_config(
    page_title='Biomarkers',
    page_icon=':material/biotech:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.session_state.setdefault('token', '')

st.session_state.setdefault('biomarkers_loaded', False)
st.session_state.setdefault('biomarker_units_loaded', False)

if not st.session_state.get('token', ''):
    st.error('Please log in to access patient biomarkers.')
    st.stop()


if not st.session_state.get('patient_ids'):
    st.error('No patients available. Please add a patient first.')
    st.stop()


if st.session_state.get('patient_id') == 0:
    st.error('Please select a patient to proceed.')
    st.stop()

st.title('🔬 Biomarkers')

if not st.session_state.biomarkers_loaded:
    try:
        with st.spinner('Loading biomarker metadata...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/biomarkers',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
            biomarkers: list[dict[str, str]
                             ] = response.json().get('biomarkers', [])
            st.session_state.biomarkers = biomarkers
            st.session_state.biomarkers_loaded = True
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching biomarkers: {error_detail}')
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()

if not st.session_state.biomarker_units_loaded:
    try:
        with st.spinner('Loading biomarker units...', show_time=True):
            response = requests.get(headers={'Authorization': f'Bearer {st.session_state.token}'},
                                    url=f'{FAST_API_BASE_URL}/api/biomarkers/units',
                                    timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT))
            response.raise_for_status()
            biomarker_units: dict[str, list[str]] = response.json().get(
                'biomarker_units', {})
            st.session_state.biomarker_units = biomarker_units
            st.session_state.biomarker_units_loaded = True
    except HTTPError:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f'Error fetching biomarker units: {error_detail}')
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()

checkboxes: dict[str, bool] = {}

biomarkers: list[dict[str, str]] = sorted(
    st.session_state.get('biomarkers', []), key=lambda x: x['abbreviation'])

biomarker_std_units: dict[str, str] = {
    biomarker['abbreviation']: biomarker['standard_unit'] for biomarker in biomarkers
}

cols = st.columns(5, gap='large', border=False)


patient_id: int = st.session_state.get('patient_id')
index: int = st.session_state.get('patient_ids', []).index(patient_id)
cols[0].selectbox(label='Select patient',
                  key='biomarkers_selectbox',
                  options=st.session_state.get('patient_ids'),
                  index=index)


def reset_button() -> None:
    """Reset the biomarker checkboxes."""
    for biomarker_name in biomarker_names:
        st.session_state[f'{biomarker_name}_checkbox'] = False


cols[4].button(
    label='Reset',
    icon='🔄',
    key='biomarkers_reset',
    use_container_width=True,
    on_click=reset_button
)

biomarker_reference_ranges: dict[str, str] = {
    biomarker['abbreviation']:
    biomarker['reference_range'] + ' ' +
    f'({biomarker_std_units[biomarker['abbreviation']]})'
    for biomarker in biomarkers
}

biomarker_names: dict[str, str] = {
    biomarker['abbreviation']: biomarker.get('name', '')
    for biomarker in biomarkers
}


biomarker_units: dict[str, list[str]] = st.session_state.get(
    'biomarker_units', {})
for biomarker, unit in biomarker_std_units.items():
    with st.container():
        row = st.columns([2, 3, 4], gap='medium', border=False)
        if biomarker_names[biomarker]:
            checkboxes[f'{biomarker}'] = row[0].checkbox(
                label=biomarker,
                key=f'{biomarker}_checkbox',
                value=False,
                help=f"{biomarker_names[biomarker]}"
            )
        else:
            checkboxes[f'{biomarker}'] = row[0].checkbox(
                label=biomarker,
                key=f'{biomarker}_checkbox',
                value=False
            )
        row[0].caption(
            f"Reference Range: {biomarker_reference_ranges[biomarker]}")
    if checkboxes[f'{biomarker}']:
        row[1].number_input(
            label='',
            key=f'{biomarker}_value',
            min_value=0.0,
            step=0.01,
            format='%.2f',
            width='stretch'
        )
        if 'ratio' not in biomarker_units.get(biomarker):
            row[2].selectbox(
                key=f'{biomarker}_unit',
                label='',
                options=biomarker_units.get(biomarker, []),
                index=0
            )

btn_cols = st.columns(5, gap='medium')
submitted = btn_cols[-1].button(
    label='Next',
    use_container_width=True,
    icon='➡️'
)


biomarker_value_unit: dict[str, tuple[float, str]] = {}
for biomarker, flag in checkboxes.items():
    if flag:
        biomarker_value_unit[biomarker] = (
            st.session_state.get(f'{biomarker}_value', 0.0),
            st.session_state.get(f'{biomarker}_unit', 'Please select')
        )


patient_id: int = st.session_state.get('patient_id')
if submitted:
    try:
        with st.spinner('Submitting biomarkers...', show_time=True):
            patient_biomarkers_request = {
                'biomarker_value_unit': biomarker_value_unit
            }
            time.sleep(5)
            response = requests.post(
                json=patient_biomarkers_request,
                headers={'Authorization': f'Bearer {st.session_state.token}'},
                url=f"{FAST_API_BASE_URL}/api/patients/{patient_id}/biomarkers",
                timeout=(FAST_API_CONNECT_TIMEOUT, FAST_API_READ_TIMEOUT)
            )
            response.raise_for_status()
        st.success('Patient biomarkers submitted successfully!')
        time.sleep(2)
        st.session_state.biomarkers_loaded = False
        st.switch_page('./pages/6_Results.py')
    except requests.exceptions.ConnectionError:
        st.error('Please check your internet connection or try again later.')
        st.stop()
