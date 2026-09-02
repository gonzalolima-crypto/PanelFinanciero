"""Operaciones sobre movimientos y configuración."""
from datetime import datetime, timezone
import re
import secrets
from typing import Optional

from .db import get_db

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Tipos de movimiento válidos (mismo modelo que el prototipo)
VALID_TYPES = {
    "gasto_diario",
    "gasto_tarjeta",
    "impuesto",
    "ingreso_sueldo",
    "ingreso_extra",
}
VALID_CURRENCIES = {"ARS", "USD"}


def _new_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(3)


def list_movements() -> list[dict]:
    rows = get_db().execute(
        "SELECT id, type, date, effective_date, category, amount, currency, note "
        "FROM movements ORDER BY date DESC, created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def add_movement(
    *,
    type: str,
    date: str,
    amount: float,
    category: Optional[str] = "",
    note: Optional[str] = "",
    effective_date: Optional[str] = None,
    currency: Optional[str] = "ARS",
) -> dict:
    if type not in VALID_TYPES:
        raise ValueError(f"tipo inválido: {type}")

    currency = (currency or "ARS").upper()
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"moneda inválida: {currency}")

    try:
        amount = round(float(amount), 2)
    except (TypeError, ValueError):
        raise ValueError("monto inválido")
    if amount == 0:
        raise ValueError("el monto no puede ser cero")
    # Los gastos pueden ser negativos (reintegro / devolución). Los ingresos no.
    if amount < 0 and type.startswith("ingreso"):
        raise ValueError("un ingreso no puede ser negativo")

    if not date or not _DATE_RE.match(date):
        raise ValueError("fecha inválida (se espera YYYY-MM-DD)")

    eff = effective_date or date
    if not _DATE_RE.match(eff):
        raise ValueError("fecha de imputación inválida (se espera YYYY-MM-DD)")

    mv = {
        "id": _new_id(),
        "type": type,
        "date": date,
        "effective_date": eff,
        "category": (category or "").strip(),
        "amount": amount,
        "currency": currency,
        "note": (note or "").strip(),
    }
    db = get_db()
    db.execute(
        "INSERT INTO movements(id, type, date, effective_date, category, amount, currency, note, created_at) "
        "VALUES (:id, :type, :date, :effective_date, :category, :amount, :currency, :note, :created_at)",
        {**mv, "created_at": datetime.now(timezone.utc).isoformat()},
    )
    db.commit()
    return mv


def delete_movement(movement_id: str) -> bool:
    db = get_db()
    cur = db.execute("DELETE FROM movements WHERE id = ?", (movement_id,))
    db.commit()
    return cur.rowcount > 0


def get_config() -> dict:
    rows = get_db().execute("SELECT key, value FROM config").fetchall()
    out: dict = {}
    for r in rows:
        out[r["key"]] = r["value"]
    # goalPct como número para el frontend
    try:
        out["goalPct"] = float(out.get("goalPct", 20))
    except (TypeError, ValueError):
        out["goalPct"] = 20.0
    return out


def set_config(key: str, value: str) -> None:
    db = get_db()
    db.execute(
        "INSERT INTO config(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    db.commit()
