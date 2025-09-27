import os
from pydantic import BaseModel
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import function_tool

class EmailResponse(BaseModel):
    status_code: int
    body: str

@function_tool(strict_mode=False)
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body to all sales prospects """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("a204g91@outlook.com")  # Change to your verified sender
    to_email = To("abhigl91@gmail.com")  # Change to your recipient
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
    return {"status": "success"}
