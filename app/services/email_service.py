import os
from pathlib import Path
import httpx
from jinja2 import Environment, FileSystemLoader
from settings import get_settings

BASE_DIR = Path(__file__).resolve().parent.parent
template_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates/"))
)

settings = get_settings()

EMAIL_LOGO = "https://res.cloudinary.com/dxzjdyf5z/image/upload/v1769970393/vogydvsazh9etigf9ww5.png"
RESEND_API_URL = "https://api.resend.com/emails"


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

        payload = {
            "from": settings.resend_from_email,
            "to": recipient if isinstance(recipient, list) else [recipient],
            "subject": subject,
            "html": html_content,
        }
        headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(RESEND_API_URL, json=payload, headers=headers)
            response.raise_for_status()


def get_email_service() -> EmailService:
    return EmailService()
