import os
import json
import base64
import uuid
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_credentials():
    """
    Carga credenciales del service account sin impersonación.
    El acceso al calendario es via compartir directamente con el service account.
    """
    sa_b64 = os.getenv("SERVICE_ACCOUNT_JSON_B64")

    if sa_b64:
        info = json.loads(base64.b64decode(sa_b64))
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )

    sa_path = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "service_account.json",
        )
    )
    return service_account.Credentials.from_service_account_file(
        sa_path, scopes=SCOPES
    )


def get_calendar_service():
    creds = _get_credentials()
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def register_watch(calendar_id: str, webhook_url: str) -> dict:
    """
    Registra un canal de notificaciones push.
    calendar_id es el email del usuario que compartió su calendario
    con el service account.
    """
    service = get_calendar_service()
    body = {
        "id": str(uuid.uuid4()),
        "type": "web_hook",
        "address": webhook_url,
    }
    return service.events().watch(calendarId=calendar_id, body=body).execute()


def list_updated_events(calendar_id: str, minutes_back: int = 3) -> list:
    """Devuelve eventos futuros actualizados en los últimos N minutos."""
    service = get_calendar_service()
    now = datetime.now(timezone.utc)
    updated_min = (now - timedelta(minutes=minutes_back)).isoformat()

    result = service.events().list(
        calendarId=calendar_id,
        updatedMin=updated_min,
        timeMin=now.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    return result.get("items", [])
