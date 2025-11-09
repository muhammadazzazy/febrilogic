from datetime import datetime

import streamlit as st

from config import FEBRILOGIC_LOGO


st.set_page_config(
    page_title='Privacy Policy',
    page_icon=':material/privacy_tip:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('🛡️ Privacy Policy')

st.logo(FEBRILOGIC_LOGO, size='large', link='https://www.febrilogic.com')

st.header(f'Effective Date: {datetime.now().date().strftime("%d-%m-%Y")}')
st.markdown(
    """FebriLogic ("we", "our", or "us") respects your privacy and is committed to protecting your personal data and the data you enter into our application (the “App”).
By using the App, you agree to the practices described in this Privacy Policy.

### 1. Data Controller

FebriLogic

Email: support@febrilogic.com

### 2. Information We Collect

We collect the following categories of information:

a. User Data (Healthcare Professionals)

- Email address and password (for account creation and login)
- Password reset requests (reset token and new password, stored securely)

b. Patient Data (entered by users)
- Demographics: age, sex, country, city, race
- Clinical information: negative test results for diseases, symptoms, biomarkers (with values and units)

### 3. Legal Basis for Processing
We process personal data under the following GDPR legal bases:

- **Contract (Art. 6(1)(b) GDPR)**: To create and maintain your account, provide services, and enable password reset.
- **Legitimate Interests (Art. 6(1)(f) GDPR)**: To improve, maintain, and secure our services.
- **Consent (Art. 6(1)(a) GDPR)**: Where you voluntarily input patient data into the App for analysis.
- **Special Category Data (Art. 9(2)(a) GDPR)**: Processing of health-related information is based on your **explicit consent** when entering patient data into the App.

You may withdraw your consent at any time by deleting patient entries or contacting us.
### 4. How We Use Data

We use collected information to:
- Provide account registration, authentication, and password reset functionality.
- Enable healthcare professionals to record patient demographics, symptoms, biomarkers, and test results.
- Improve and secure the App.

### 5. Data Sharing and Transfers
- **Service Providers**: We may share data with IT and hosting providers to operate the App.
- **Legal Requirements**: We may disclose data if required by applicable law or regulation.
- **International Transfers**: Some data may be transferred outside the European Economic Area (EEA). Where this occurs, we ensure adequate safeguards are in place (e.g., EU Standard Contractual Clauses).

We do not sell or rent user or patient data to third parties.
    
### 6. Data Retention
    
- User account data: kept as long as your account is active.
- Backups or logs may be stored for a limited period before secure deletion.
    
### 7. Data Security
- User passwords are hashed and salted before storage.
- All communications are encrypted (TLS/HTTPS).
- Access to data is limited to authorized personnel.
    
### 8. Your GDPR Rights

Under GDPR, you have the following rights:

- **Access:** Obtain a copy of your personal data.
- **Rectification:** Correct inaccurate or incomplete data.
- **Erasure (“Right to be Forgotten”):** Request deletion of your data.
- **Restriction of Processing:** Limit how we use your data.
- **Data Portability:** Request transfer of your data to another provider.
- **Objection:** Object to processing based on legitimate interests.
- **Withdraw Consent:** Withdraw consent at any time without affecting prior lawful processing.

To exercise these rights, contact us at: support@febrilogic.com.

### 9. Children’s Privacy

FebriLogic is intended for healthcare professionals only.
It is not directed at children under 16, 
and we do not knowingly collect personal data directly from children.

### 10. Changes to This Privacy Policy

We may update this Privacy Policy from time to time. 
Updates will be posted within the App, with the “Effective Date” updated accordingly. 
Continued use of the App after changes indicates acceptance.
"""
)
