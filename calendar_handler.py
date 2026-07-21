from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH, setup_google_files

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def _get_service():
    setup_google_files()
    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    return build("calendar", "v3", credentials=creds)


def get_events(date_str: str, days: int = 0) -> str:
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(date_str, "%Y-%m-%d")
    end = start + timedelta(days=days + 1) if days > 0 else start + timedelta(days=1)

    service = _get_service()
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat() + "Z",
        timeMax=end.isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    if not events:
        return "No hay eventos en esa fecha."

    lines = []
    for e in events:
        start_str = e["start"].get("dateTime", e["start"].get("date", ""))
        summary = e.get("summary", "Sin titulo")
        lines.append(f"- {start_str}: {summary}")

    return "\n".join(lines)


def create_event(summary: str, date_str: str, time_str: str, duration_hours: float = 1.0) -> str:
    from datetime import datetime

    service = _get_service()
    dt_start = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M")
    dt_end = dt_start.replace(hour=dt_start.hour + int(duration_hours))
    dt_end = dt_end + timedelta(minutes=int((duration_hours % 1) * 60))

    event = {
        "summary": summary,
        "start": {
            "dateTime": dt_start.isoformat(),
            "timeZone": "America/Argentina/Buenos_Aires",
        },
        "end": {
            "dateTime": dt_end.isoformat(),
            "timeZone": "America/Argentina/Buenos_Aires",
        },
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Evento creado: {summary} el {date_str} a las {time_str}"
