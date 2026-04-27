from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta

from services.scraper_service import get_company_brief
from services.mock_data import get_mock_brief
from services.scheduler import scheduler
from services.email_service import send_brief_email

router = APIRouter()


class MeetingRequest(BaseModel):
    company: str
    participants: List[str]
    meeting_datetime: str
    email: Optional[EmailStr] = None  # destinatario del brief


class MeetingResponse(BaseModel):
    status: str
    meeting: dict
    brief: dict
    email_scheduled: bool
    email_send_at: Optional[str] = None


@router.post("/meeting/trigger", response_model=MeetingResponse)
async def trigger_meeting_prep(payload: MeetingRequest):
    """
    Genera el AI Brief y programa el envío del correo 24h antes de la reunión.
    """
    try:
        brief = get_company_brief(payload.company)
    except Exception as e:
        print(f"[scraper] Falló scraping, usando mock: {e}")
        brief = get_mock_brief(payload.company)

    meeting_data = {
        "company": payload.company,
        "participants": payload.participants,
        "datetime": payload.meeting_datetime,
    }

    email_scheduled = False
    email_send_at = None

    if payload.email:
        try:
            meeting_dt = datetime.fromisoformat(payload.meeting_datetime)
            send_at = meeting_dt - timedelta(hours=24)
            now = datetime.now()

            if send_at > now:
                # Programar para 24h antes
                scheduler.add_job(
                    send_brief_email,
                    trigger="date",
                    run_date=send_at,
                    args=[payload.email, meeting_data, brief],
                    id=f"brief_{payload.company}_{payload.meeting_datetime}",
                    replace_existing=True,
                )
                email_scheduled = True
                email_send_at = send_at.isoformat()
                print(f"[scheduler] Email programado para {send_at} → {payload.email}")
            elif meeting_dt > now:
                # La reunión es en menos de 24h → enviar ahora
                scheduler.add_job(
                    send_brief_email,
                    trigger="date",
                    run_date=now + timedelta(seconds=5),
                    args=[payload.email, meeting_data, brief],
                    id=f"brief_immediate_{payload.company}",
                    replace_existing=True,
                )
                email_scheduled = True
                email_send_at = (now + timedelta(seconds=5)).isoformat()
                print(f"[scheduler] Reunión en <24h — enviando brief ahora → {payload.email}")
            else:
                print(f"[scheduler] Reunión en el pasado, no se programa email.")

        except Exception as exc:
            print(f"[scheduler] Error al programar email: {exc}")

    return {
        "status": "success",
        "meeting": meeting_data,
        "brief": brief,
        "email_scheduled": email_scheduled,
        "email_send_at": email_send_at,
    }


@router.get("/email/config")
async def check_email_config():
    """Verifica qué credenciales SMTP está leyendo el servidor."""
    import os
    user = os.getenv("SMTP_USER", "NO CONFIGURADO")
    pwd = os.getenv("SMTP_PASSWORD", "")
    return {
        "smtp_host": os.getenv("SMTP_HOST", "NO CONFIGURADO"),
        "smtp_port": os.getenv("SMTP_PORT", "NO CONFIGURADO"),
        "smtp_user": user,
        "smtp_password_preview": f"{pwd[:4]}...{pwd[-4:]}" if len(pwd) > 8 else "MUY CORTA O VACÍA",
        "smtp_password_len": len(pwd),
    }


@router.post("/email/test")
async def test_email(payload: dict):
    """
    Envía un correo de prueba inmediatamente.
    Body: { "email": "destino@ejemplo.com" }
    """
    to_email = payload.get("email")
    if not to_email:
        return {"status": "error", "detail": "Falta el campo 'email'"}

    brief = get_mock_brief("ACME Corp")
    meeting_data = {
        "company": "ACME Corp",
        "participants": ["Laura Gómez", "Mario Ruiz"],
        "datetime": "2026-04-16T10:00:00",
    }

    try:
        send_brief_email(to_email, meeting_data, brief)
        return {"status": "ok", "detail": f"Correo enviado a {to_email}"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/meeting/demo")
async def get_demo_brief():
    """Brief de demo para ACME Corp (sin scheduling)."""
    brief = get_mock_brief("ACME Corp")
    return {
        "status": "success",
        "meeting": {
            "company": "ACME Corp",
            "participants": ["Laura Gómez", "Mario Ruiz", "Ana Torres"],
            "datetime": "2026-04-16T10:00:00",
        },
        "brief": brief,
        "email_scheduled": False,
        "email_send_at": None,
    }
