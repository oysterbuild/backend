import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader
from settings import get_settings
from fastapi import Request

# Get the path to the templates folder
BASE_DIR = Path(__file__).resolve().parent.parent
template_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates/"))
)

settings = get_settings()

EMAIL_LOGO = "https://res.cloudinary.com/dxzjdyf5z/image/upload/v1769970393/vogydvsazh9etigf9ww5.png"


class EmailService:

    def __init__(self):
        # Configuration for SMTP
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.email_host_user,
            MAIL_PASSWORD=settings.email_host_password,
            MAIL_FROM=settings.email_host_user,
            MAIL_PORT=587,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
        )

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

        # 2. Create the message
        message = MessageSchema(
            subject=subject,
            recipients=recipient,
            body=html_content,
            subtype=MessageType.html,
        )

        # 3. Send via FastMail
        fm = FastMail(self.conf)
        await fm.send_message(message)


def get_email_service() -> EmailService:
    return EmailService()
