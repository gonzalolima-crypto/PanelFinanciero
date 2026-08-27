"""Configuración central de la aplicación.

Todos los valores se leen de variables de entorno (archivo .env en local,
secrets de Fly.io en producción). Nunca escribas claves reales acá.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Carpeta raíz del proyecto (un nivel arriba de /app)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga el archivo .env si existe (en producción no existe y no pasa nada)
load_dotenv(BASE_DIR / ".env")


def _as_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


# --- Rutas de datos ---------------------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = os.environ.get("DB_PATH", str(DATA_DIR / "panel.db"))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(DATA_DIR / "uploads")))

# --- Seguridad -------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-cambiar")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "").strip()

# --- Gemini --------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

# --- Límites -------------------------------------------------------------
MAX_CONTENT_MB = _as_int("MAX_CONTENT_MB", 25)
MAX_CONTENT_LENGTH = MAX_CONTENT_MB * 1024 * 1024

PORT = _as_int("PORT", 8000)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
