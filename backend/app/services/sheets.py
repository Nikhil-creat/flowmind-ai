from loguru import logger

from app.core.config import get_settings

settings = get_settings()

_sheets_service = None


def _get_service():
    """Lazily builds an authenticated Sheets API client from a service
    account JSON file. Returns None (and logs) if not configured, so the
    calling workflow node degrades gracefully instead of crashing the run."""
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service

    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        _sheets_service = build("sheets", "v4", credentials=credentials)
        return _sheets_service
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Google Sheets client init failed: {exc}")
        return None


def append_row(spreadsheet_id: str, range_name: str, values: list) -> str:
    """Appends one row of values to a Google Sheet. `values` is a flat list
    of cell values, e.g. ["2026-09-06", "Nikhil", "Signed up"]."""
    service = _get_service()
    if not service:
        logger.info(f"[sheets] Not configured - would append {values} to {spreadsheet_id}!{range_name}")
        return "not sent (Google Sheets not configured)"

    try:
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()
        return "appended"
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Google Sheets append failed: {exc}")
        return f"failed: {exc}"
