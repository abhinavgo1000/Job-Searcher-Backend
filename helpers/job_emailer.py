import os
from pydantic import BaseModel
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import function_tool

class EmailResponse(BaseModel):
    status_code: int
    body: str

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

@function_tool(strict_mode=False)
def send_shortlisted_jobs_email(jobs: list[dict], subject: str = "Your Shortlisted Jobs") -> EmailResponse:
    """
    Send an email with the shortlisted jobs using SendGrid.
    """
    from_email = Email("a204g91@outlook.com")
    to_email = To("abhigl91@gmail.com")
    job_lines = []
    for job in jobs:
        line = f"{job.get('title', 'Job')} at {job.get('company', '')} - {job.get('location', '')}\n{job.get('url', '')}\n"
        job_lines.append(line)
    content_str = "\n\n".join(job_lines) if job_lines else "No jobs shortlisted."
    content = Content("text/plain", content_str)
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return EmailResponse(
        status_code=response.status_code,
        body=response.body.decode()
    )
