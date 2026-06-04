import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from config import GOOGLE_CALENDAR_ID, GOOGLE_CREDENTIALS_FILE, RESTAURANT_NAME, TIMEZONE

logger = logging.getLogger(__name__)

_service = None
_calendar = None


def _get_calendar():
    global _service, _calendar
    if _calendar is not None:
        return _calendar

    creds_path = Path(GOOGLE_CREDENTIALS_FILE)
    if not creds_path.exists() or not GOOGLE_CALENDAR_ID:
        logger.warning("Google Calendar non configurato — modalità locale attiva")
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=scopes
        )
        _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        _calendar = _service
        return _calendar
    except Exception as exc:
        logger.error("Errore init Google Calendar: %s", exc)
        return None


def _parse_dt(date_str: str, time_str: str) -> datetime:
    tz = ZoneInfo(TIMEZONE)
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)


def count_calendar_bookings(date_str: str, slot: str) -> int:
    """Conta eventi nel calendario per quella data/fascia."""
    cal = _get_calendar()
    if not cal:
        return 0

    from config import SLOT_HOURS

    start_h, end_h = SLOT_HOURS[slot]
    tz = ZoneInfo(TIMEZONE)
    day = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    time_min = day.replace(hour=start_h, minute=0).isoformat()
    time_max = day.replace(hour=end_h, minute=0).isoformat()

    try:
        events = (
            cal.events()
            .list(
                calendarId=GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return len(events.get("items", []))
    except Exception as exc:
        logger.error("Errore lettura calendario: %s", exc)
        return 0


def create_event(
    guest_name: str,
    guests: int,
    date_str: str,
    time_str: str,
    slot: str,
    table_label: str,
    occasion: str | None = None,
    upsells: list | None = None,
    telegram_user: str | None = None,
) -> str | None:
    cal = _get_calendar()
    if not cal:
        return None

    start = _parse_dt(date_str, time_str)
    end = start + timedelta(hours=2)
    tz = ZoneInfo(TIMEZONE)

    extras = ""
    if occasion:
        extras += f"\nOccasione: {occasion}"
    if upsells:
        extras += f"\nExtra: {', '.join(upsells)}"
    if telegram_user:
        extras += f"\nTelegram: {telegram_user}"

    body = {
        "summary": f"[Prenotazione] {guest_name} — {guests} pers.",
        "location": RESTAURANT_NAME,
        "description": (
            f"Prenotazione sushi\n"
            f"Nome: {guest_name}\n"
            f"Persone: {guests}\n"
            f"Tavolo: {table_label}\n"
            f"Fascia: {slot}{extras}"
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end.astimezone(tz).isoformat(), "timeZone": TIMEZONE},
        "colorId": "4",
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},
                {"method": "popup", "minutes": 180},
            ],
        },
    }

    try:
        event = cal.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=body).execute()
        return event.get("id")
    except Exception as exc:
        logger.error("Errore creazione evento: %s", exc)
        return None


def delete_event(event_id: str) -> bool:
    cal = _get_calendar()
    if not cal or not event_id:
        return False
    try:
        cal.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=event_id).execute()
        return True
    except Exception as exc:
        logger.error("Errore eliminazione evento: %s", exc)
        return False


def is_configured() -> bool:
    return Path(GOOGLE_CREDENTIALS_FILE).exists() and bool(GOOGLE_CALENDAR_ID)
