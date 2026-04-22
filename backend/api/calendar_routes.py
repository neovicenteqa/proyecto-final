import os
from fastapi import APIRouter, BackgroundTasks, Request, Header
from typing import Optional
from datetime import datetime, timedelta, timezone

from services.mock_data import get_mock_brief
from services.scheduler import scheduler
from services.email_service import send_brief_email

router = APIRouter()


# ── Registro del webhook ──────────────────────────────────────────────────────

@router.post("/calendar/watch")
async def register_calendar_watch(payload: dict):
    """
    Registra el watch de Google Calendar para un usuario.
    Body: { "user_email": "...", "webhook_url": "https://tu-app/api/calendar/webhook" }
    """
    from services.calendar_service import register_watch

    user_email = payload.get("user_email")
    webhook_url = payload.get("webhook_url")

    if not user_email or not webhook_url:
        return {"status": "error", "detail": "Faltan campos: user_email, webhook_url"}

    try:
        result = register_watch(
            calendar_id=user_email,
            webhook_url=webhook_url,
        )

        channel_id = result["id"]
        expiration_ms = int(result.get("expiration", 0))
        expiration_dt = (
            datetime.fromtimestamp(expiration_ms / 1000).isoformat()
            if expiration_ms else "desconocido"
        )

        print(f"[calendar] Watch registrado para {user_email} — expira {expiration_dt}")
        return {
            "status": "ok",
            "channel_id": channel_id,
            "expiration": expiration_dt,
            "message": f"Escuchando calendario de {user_email}. Expira: {expiration_dt}",
        }

    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ── Receptor de notificaciones de Google ─────────────────────────────────────

@router.post("/calendar/webhook")
async def calendar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_goog_resource_state: Optional[str] = Header(None),
    x_goog_channel_id: Optional[str] = Header(None),
):
    """
    Google Calendar envía un POST aquí cada vez que hay un cambio en el calendario.
    Debe responder 200 inmediatamente; el procesamiento va en background.
    """
    if x_goog_resource_state == "sync":
        print(f"[calendar] Sync recibido para canal {x_goog_channel_id}")
        return {"status": "ok"}

    if x_goog_resource_state == "exists":
        user_email = os.getenv("CALENDAR_USER_EMAIL", "")
        if user_email:
            print(f"[calendar] Notificación recibida — procesando calendario de {user_email}")
            background_tasks.add_task(
                _process_calendar_update,
                user_email,
                user_email,
            )
        else:
            print("[calendar] ERROR: variable CALENDAR_USER_EMAIL no configurada")

    return {"status": "ok"}


# ── Procesamiento en background ───────────────────────────────────────────────

async def _process_calendar_update(calendar_id: str, user_email: str):
    from services.calendar_service import list_updated_events

    try:
        events = list_updated_events(calendar_id)

        for event in events:
            _schedule_brief_for_event(event, user_email)

    except Exception as exc:
        print(f"[calendar] Error procesando update para {user_email}: {exc}")


def _get_kam_list() -> set:
    """Lee la lista de KAMs desde la variable de entorno BRIEF_RECIPIENTS."""
    raw = os.getenv("BRIEF_RECIPIENTS", "")
    return {email.strip().lower() for email in raw.split(",") if email.strip()}


def _schedule_brief_for_event(event: dict, triggered_by: str):
    summary = event.get("summary", "Reunión")
    start = event.get("start", {})
    start_str = start.get("dateTime") or start.get("date")
    attendees = event.get("attendees", [])
    status = event.get("status", "confirmed")

    if status == "cancelled" or not start_str:
        return

    kam_list = _get_kam_list()

    # KAMs que están invitados a esta reunión (intersección entre asistentes y lista KAM)
    attendee_emails = {
        a["email"].lower()
        for a in attendees
        if a.get("email") and not a.get("resource", False)
    }

    if kam_list:
        recipients = kam_list & attendee_emails
    else:
        # Si no hay lista configurada, enviar a todos los @neo.com.pe del evento
        recipients = {e for e in attendee_emails if e.endswith("@neo.com.pe")}

    if not recipients:
        print(f"[calendar] '{summary}' — ningún KAM invitado, no se envía brief")
        return

    # Parsear fecha
    try:
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        start_dt_local = start_dt.replace(tzinfo=None)
    except ValueError:
        print(f"[calendar] No se pudo parsear fecha: {start_str}")
        return

    brief = get_mock_brief(summary)
    meeting_data = {
        "company": summary,
        "participants": [
            a.get("displayName") or a.get("email") for a in attendees
        ],
        "datetime": start_dt_local.isoformat(),
    }

    send_at = start_dt_local - timedelta(hours=24)
    now = datetime.now()

    for email in recipients:
        run_at = send_at if send_at > now else now + timedelta(seconds=10)

        scheduler.add_job(
            send_brief_email,
            trigger="date",
            run_date=run_at,
            args=[email, meeting_data, brief],
            id=f"cal_{event['id']}_{email}",
            replace_existing=True,
        )
        label = "programado" if send_at > now else "enviando ahora"
        print(f"[calendar] Brief {label} → {email} | '{summary}' el {start_dt_local}")
