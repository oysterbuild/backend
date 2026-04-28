import os
import asyncio
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from settings import get_settings

BASE_DIR = Path(__file__).resolve().parent.parent
template_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates/"))
)

settings = get_settings()

EMAIL_LOGO = "https://res.cloudinary.com/dxzjdyf5z/image/upload/v1769970393/vogydvsazh9etigf9ww5.png"


class EmailService:

    async def send_emails(
        self,
        subject: str,
        recipient: list,
        template_name: str,
        context: dict,
    ):
        template = template_env.get_template(template_name)
        context["logo_url"] = EMAIL_LOGO
        html_content = template.render(**context)

        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=recipient,
            subject=subject,
            html_content=html_content,
        )

        def _send():
            sg = SendGridAPIClient(settings.sendgrid_api_key)
            sg.send(message)

        await asyncio.to_thread(_send)


def get_email_service() -> EmailService:
    return EmailService()
