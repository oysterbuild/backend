import secrets
import string


def email_nomalizers(email: str):
    return email.lower()


def generate_otp_pin(digit: int = 4) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(digit))
