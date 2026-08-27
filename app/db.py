"""Acceso a la base de datos SQLite.

Tablas:
  movements(id, type, date, category, amount, note, created_at)
  config(key, value)
"""
import sqlite3
from typing import Any

from flask import g

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS movements (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,
    date        TEXT NOT NULL,
    category    TEXT,
    amount      REAL NOT NULL,
    note        TEXT,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_movements_date ON movements(date);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

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
        for key, value in DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO config(key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()
    finally:
        conn.close()
