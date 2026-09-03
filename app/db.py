"""Acceso a la base de datos.

Soporta dos motores, según la variable de entorno DATABASE_URL:

  - **SQLite** (por defecto): archivo `data/panel.db`. Es lo que se usa cuando
    corrés la app en tu computadora con `iniciar.bat`.
  - **PostgreSQL**: si DATABASE_URL empieza con `postgres://` o `postgresql://`.
    Es lo que se usa en producción (Render + Neon), porque el disco del hosting
    gratuito se borra en cada reinicio.

Tablas:
  movements(id, type, date, effective_date, category, amount, currency, note, created_at)
  config(key, value)

`date`            = fecha real del movimiento / de la compra.
`effective_date`  = fecha con la que se imputa a un mes. Para casi todo es
                    igual a `date`; para los consumos de un resumen de tarjeta
                    es la fecha de vencimiento del resumen (ahí se paga).

El resto de la app usa sólo `fetchall()` y `execute()`, así que no le importa
qué motor hay debajo. Las consultas se escriben con parámetros con nombre
(`:nombre`) y acá se traducen al formato de cada motor.
"""
import re
import sqlite3
from typing import Any, Optional

from flask import g

from . import config

IS_PG = config.DATABASE_URL.startswith(("postgres://", "postgresql://"))

_AMOUNT_TYPE = "DOUBLE PRECISION" if IS_PG else "REAL"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS movements (
    id             TEXT PRIMARY KEY,
    type           TEXT NOT NULL,
    date           TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    category       TEXT,
    amount         {_AMOUNT_TYPE} NOT NULL,
    currency       TEXT NOT NULL DEFAULT 'ARS',
    note           TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_movements_date ON movements(date);
CREATE INDEX IF NOT EXISTS idx_movements_effdate ON movements(effective_date);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_CONFIG = {
    "goalPct": "20",
}

# --- Traducción de parámetros ------------------------------------------
# Las consultas se escriben con :nombre (estilo SQLite). psycopg usa %(nombre)s.
_NAMED_PARAM = re.compile(r"(?<!:):([A-Za-z_]\w*)")


def _adapt(sql: str) -> str:
    return _NAMED_PARAM.sub(r"%(\1)s", sql) if IS_PG else sql


# --- Conexión ----------------------------------------------------------

_pool = None


def _get_pool():
    """Pool de conexiones Postgres (se crea una sola vez)."""
    global _pool
    if _pool is None:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        _pool = ConnectionPool(
            config.DATABASE_URL,
            min_size=1,
            max_size=4,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


def get_db():
    """Conexión asociada al request actual."""
    if "db_conn" not in g:
        if IS_PG:
            g.db_cm = _get_pool().connection()
            g.db_conn = g.db_cm.__enter__()
        else:
            conn = sqlite3.connect(config.DB_PATH)
            conn.row_factory = sqlite3.Row
            g.db_conn = conn
    return g.db_conn


def close_db(_exc: Any = None) -> None:
    conn = g.pop("db_conn", None)
    cm = g.pop("db_cm", None)
    if cm is not None:          # Postgres: devolver la conexión al pool
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass
    elif conn is not None:      # SQLite
        conn.close()


# --- Helpers de consulta ------------------------------------------------

def fetchall(sql: str, params: Optional[dict] = None) -> list[dict]:
    conn = get_db()
    if IS_PG:
        with conn.cursor() as cur:
            cur.execute(_adapt(sql), params or {})
            return [dict(r) for r in cur.fetchall()]
    cur = conn.execute(sql, params or {})
    return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params: Optional[dict] = None) -> int:
    """Ejecuta una sentencia de escritura y devuelve las filas afectadas."""
    conn = get_db()
    if IS_PG:
        with conn.cursor() as cur:
            cur.execute(_adapt(sql), params or {})
            n = cur.rowcount
        conn.commit()
        return n
    cur = conn.execute(sql, params or {})
    conn.commit()
    return cur.rowcount


# --- Creación / migración ------------------------------------------------

def _migrate_sqlite(conn: sqlite3.Connection) -> None:
    """Agrega columnas nuevas a bases SQLite creadas con versiones anteriores."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(movements)")}
    if "effective_date" not in cols:
        conn.execute("ALTER TABLE movements ADD COLUMN effective_date TEXT")
        conn.execute(
            "UPDATE movements SET effective_date = date "
            "WHERE effective_date IS NULL OR effective_date = ''"
        )
    if "currency" not in cols:
        conn.execute("ALTER TABLE movements ADD COLUMN currency TEXT NOT NULL DEFAULT 'ARS'")
        conn.execute("UPDATE movements SET currency = 'ARS' WHERE currency IS NULL OR currency = ''")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_movements_effdate ON movements(effective_date)")


_SEED_CONFIG = (
    "INSERT INTO config(key, value) VALUES (:key, :value) "
    "ON CONFLICT (key) DO NOTHING"
)


def init_db() -> None:
    """Crea las tablas si no existen. Se llama al arrancar la app."""
    if IS_PG:
        pool = _get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                for stmt in filter(None, (s.strip() for s in SCHEMA.split(";"))):
                    cur.execute(stmt)
                for key, value in DEFAULT_CONFIG.items():
                    cur.execute(_adapt(_SEED_CONFIG), {"key": key, "value": value})
            conn.commit()
        return

    config.ensure_dirs()
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.executescript(SCHEMA)
        _migrate_sqlite(conn)
        for key, value in DEFAULT_CONFIG.items():
            conn.execute(_SEED_CONFIG, {"key": key, "value": value})
        conn.commit()
    finally:
        conn.close()
