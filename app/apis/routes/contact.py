"""Send emails to the support team."""
from datetime import datetime

import resend
from fastapi import APIRouter, HTTPException
from jinja2 import Template
from starlette import status

from apis.models.contact_request import ContactRequest
from apis.config import RESEND_API_KEY, RESEND_MAX_RETRIES, SUPPORT_REQUEST_TEMPLATE


api_router: APIRouter = APIRouter(
    prefix='/api/contact',
    tags=['contact']
)

resend.api_key = RESEND_API_KEY


@api_router.post('')
def contact(contact_request: ContactRequest) -> dict[str, str]:
    """Send a contact request email."""
    with open(SUPPORT_REQUEST_TEMPLATE, encoding='utf-8') as file:
        template = Template(file.read())
    html = template.render(name=contact_request.name,
                           email=contact_request.email,
                           message=contact_request.message,
                           current_year=datetime.now().year)
    params: resend.Emails.SendParams = {
        "from": "FebriLogic <noreply@febrilogic.com>",
        "to": "FebriLogic Support <support@febrilogic.com>",
        "subject": contact_request.subject,
        "html": html
    }
    for _i in range(RESEND_MAX_RETRIES):
        email: resend.Email = resend.Emails.send(params)
        if email and 'id' in email:
            print(f"Contact request email ID: {email['id']}")
            return {
                'message': f"Contact request email {email['id']} sent successfully"
            }
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail='Failed to send contact request email after 3 attempts'
    )
