import httpx
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


def send_whatsapp(to: str, body: str) -> str:
    """Sends a WhatsApp message via Twilio. `to` should be a phone number
    like '+919876543210' - the 'whatsapp:' prefix is added automatically.
    Logs instead of failing if Twilio isn't configured."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM):
        logger.info(f"[whatsapp] Twilio not configured - would send to={to}: {body!r}")
        return "not sent (Twilio not configured)"

    try:
        to_addr = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        resp = httpx.post(
            f"{TWILIO_API_BASE}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={"From": settings.TWILIO_WHATSAPP_FROM, "To": to_addr, "Body": body},
            timeout=10,
        )
        resp.raise_for_status()
        return "sent"
    except Exception as exc:  # noqa: BLE001
        logger.error(f"WhatsApp message failed: {exc}")
        return f"failed: {exc}"
