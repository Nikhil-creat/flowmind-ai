import smtplib
from email.mime.text import MIMEText

from app.core.config import get_settings

settings = get_settings()


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email via SMTP. No-ops (logs only) if SMTP isn't configured,
    so workflows remain runnable in a fresh clone without credentials."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(f"[mailer] SMTP not configured - would send to={to} subject={subject!r}")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
        server.send_message(msg)
