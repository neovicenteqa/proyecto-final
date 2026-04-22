from fastapi import APIRouter, BackgroundTasks, Request, Header
from typing import Optional
from datetime import datetime, timedelta, timezone

from services.mock_data import get_mock_brief
from services.scheduler import scheduler
from services.email_service import send_brief_email

router = APIRouter()

# channel_id → { calendar_id, user_email }
active_watches: dict = {}


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
        active_watches[channel_id] = {
            "calendar_id": "primary",
            "user_email": user_email,
        }

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
        return {"status": "ok"}

    if x_goog_resource_state == "exists" and x_goog_channel_id:
        watch_info = active_watches.get(x_goog_channel_id)
        if watch_info:
            background_tasks.add_task(
                _process_calendar_update,
                watch_info["calendar_id"],
                watch_info["user_email"],
            )
        else:
            print(f"[calendar] Notificación de canal desconocido: {x_goog_channel_id}")

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


def _schedule_brief_for_event(event: dict, triggered_by: str):
    summary = event.get("summary", "Reunión")
    start = event.get("start", {})
    start_str = start.get("dateTime") or start.get("date")
    attendees = event.get("attendees", [])
    status = event.get("status", "confirmed")

    if status == "cancelled" or not start_str:
        return

    # Solo participantes @neo.com.pe (excluye el organizador-bot)
    neo_emails = [
        a["email"]
        for a in attendees
        if a.get("email", "").endswith("@neo.com.pe")
        and not a.get("resource", False)
    ]

    if not neo_emails:
        print(f"[calendar] Evento '{summary}' sin participantes @neo — ignorado")
        return

    # Parsear fecha
    try:
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        start_dt_local = start_dt.replace(tzinfo=None)
    except ValueError:
        print(f"[calendar] No se pudo parsear fecha: {start_str}")
        return

    # Generar brief usando el título del evento como empresa
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

    for email in neo_emails:
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
