import sys
import os

# Allow imports from the backend/ directory itself
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=os.path.normpath(env_path))

from api.routes import router
from services.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("[scheduler] APScheduler iniciado.")
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

# --- Serve frontend static files ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
FRONTEND_DIR = os.path.normpath(FRONTEND_DIR)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
