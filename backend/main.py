import sys
import os

# Allow imports from the backend/ directory itself
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=os.path.normpath(env_path))

from api.routes import router
from api.calendar_routes import router as calendar_router
from services.scheduler import scheduler


def _auto_register_watch():
    """Registra el watch de Calendar al arrancar y lo renueva cada 6 días."""
    from services.calendar_service import register_watch

    user_email = os.getenv("CALENDAR_USER_EMAIL", "")
    webhook_url = os.getenv("WEBHOOK_BASE_URL", "")

    if not user_email or not webhook_url:
        print("[calendar] CALENDAR_USER_EMAIL o WEBHOOK_BASE_URL no configurados — watch omitido")
        return

    full_webhook_url = f"{webhook_url.rstrip('/')}/api/calendar/webhook"

    try:
        result = register_watch(calendar_id=user_email, webhook_url=full_webhook_url)
        expiration_ms = int(result.get("expiration", 0))
        expiration_dt = (
            datetime.fromtimestamp(expiration_ms / 1000).isoformat()
            if expiration_ms else "desconocido"
        )
        print(f"[calendar] Watch auto-registrado para {user_email} — expira {expiration_dt}")
    except Exception as exc:
        print(f"[calendar] Error registrando watch: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("[scheduler] APScheduler iniciado.")

    # Registrar watch al arrancar
    _auto_register_watch()

    # Renovar el watch cada 6 días (expira a los 7)
    scheduler.add_job(
        _auto_register_watch,
        trigger="interval",
        days=6,
        id="watch_renewal",
        replace_existing=True,
    )

    yield
    scheduler.shutdown()
    print("[scheduler] APScheduler detenido.")


app = FastAPI(
    title="AI Brief + Smart Meeting Prep",
    description="Automatiza la preparación de reuniones con análisis de IA.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- API routes ---
app.include_router(router, prefix="/api", tags=["Meeting"])
app.include_router(calendar_router, prefix="/api", tags=["Calendar"])

# --- Serve frontend static files ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
FRONTEND_DIR = os.path.normpath(FRONTEND_DIR)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
