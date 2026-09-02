"""Acceso a la base de datos SQLite.

Tablas:
  movements(id, type, date, effective_date, category, amount, currency, note, created_at)
  config(key, value)

`date`            = fecha real del movimiento / de la compra.
`effective_date`  = fecha con la que se imputa a un mes. Para casi todo es
                    igual a `date`; para los consumos de un resumen de tarjeta
                    es la fecha de vencimiento del resumen (ahí se paga).
"""
import sqlite3
from typing import Any

from flask import g

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS movements (
    id             TEXT PRIMARY KEY,
    type           TEXT NOT NULL,
    date           TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    category       TEXT,
    amount         REAL NOT NULL,
    currency       TEXT NOT NULL DEFAULT 'ARS',
    note           TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_movements_date ON movements(date);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Migraciones simples para bases creadas con versiones anteriores."""
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

DEFAULT_CONFIG = {
    "goalPct": "20",
}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc: Any = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    config.ensure_dirs()
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        for key, value in DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO config(key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()
    finally:
        conn.close()
