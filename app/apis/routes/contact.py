"""Send emails to the support team."""
import resend
from fastapi import APIRouter, HTTPException
from starlette import status

from apis.models.contact_request import ContactRequest
from apis.config import RESEND_API_KEY, RESEND_MAX_RETRIES


api_router: APIRouter = APIRouter(
    prefix='/api/contact',
    tags=['contact']
)

resend.api_key = RESEND_API_KEY


@api_router.post('')
def contact(contact_request: ContactRequest) -> dict[str, str]:
    """Send a contact request email"""
    params: resend.Emails.SendParams = {
        "from": "FebriLogic <noreply@febrilogic.com>",
        "to": "FebriLogic Support <support@febrilogic.com>",
        "subject": contact_request.subject,
        "html": contact_request.message + f'<br>Sent by {contact_request.name} ({contact_request.email})'
    }
    for _i in range(RESEND_MAX_RETRIES):
        email: resend.Email = resend.Emails.send(params)
        if email and 'id' in email:
            print(f"Contact request email ID: {email['id']}")
            return {
                'message': f"Contact request email {email['id']} sent successfully."
            }
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail='Failed to send contact request email after 3 attempts.'
    )
