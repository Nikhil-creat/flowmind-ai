"""
Minimal Stripe Checkout integration, called directly over Stripe's REST API
(no SDK dependency needed). Entirely optional: without STRIPE_SECRET_KEY set,
callers get a clear "not configured" response instead of an error, so the
rest of the app - and the workspace/billing UI - keeps working either way.
"""
from __future__ import annotations

import httpx
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

STRIPE_API_BASE = "https://api.stripe.com/v1"


def is_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PRICE_ID_PRO)


def create_checkout_session(workspace_id: str, workspace_name: str) -> dict:
    """Creates a Stripe Checkout session for upgrading a workspace to "pro".
    Returns {"configured": False, "message": ...} if Stripe isn't set up."""
    if not is_configured():
        return {
            "configured": False,
            "checkout_url": None,
            "message": (
                "Billing isn't configured on this server yet. Set STRIPE_SECRET_KEY "
                "and STRIPE_PRICE_ID_PRO to enable real upgrades."
            ),
        }

    try:
        response = httpx.post(
            f"{STRIPE_API_BASE}/checkout/sessions",
            auth=(settings.STRIPE_SECRET_KEY, ""),
            data={
                "mode": "subscription",
                "line_items[0][price]": settings.STRIPE_PRICE_ID_PRO,
                "line_items[0][quantity]": 1,
                "success_url": f"{settings.FRONTEND_URL}/dashboard/settings?billing=success",
                "cancel_url": f"{settings.FRONTEND_URL}/dashboard/settings?billing=cancelled",
                "client_reference_id": workspace_id,
                "metadata[workspace_name]": workspace_name,
            },
            timeout=10,
        )
        response.raise_for_status()
        session = response.json()
        return {"configured": True, "checkout_url": session["url"], "message": "Checkout session created."}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Stripe checkout session creation failed: {exc}")
        return {"configured": True, "checkout_url": None, "message": f"Stripe error: {exc}"}
