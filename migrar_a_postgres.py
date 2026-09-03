"""Copia los datos de la base local (SQLite) a la base de producción (Postgres).

Cuándo usarlo: si cargaste movimientos en tu computadora y querés llevarlos a la
app publicada.

Cómo usarlo:
  1. Poné la cadena de conexión de Neon en el archivo .env, línea DATABASE_URL.
  2. Abrí PowerShell en la carpeta del proyecto y corré:

         .venv\\Scripts\\python.exe migrar_a_postgres.py

Es seguro correrlo más de una vez: los movimientos que ya estén cargados no se
duplican (se saltean por id).
"""
import sqlite3
import sys

from app import config

TABLES_MSG = "Faltan las tablas en Postgres. Arrancá la app una vez (o hacé el deploy) y volvé a intentar."


def main() -> int:
    if not config.DATABASE_URL:
        print("ERROR: DATABASE_URL está vacía. Completala en el archivo .env.")
        return 1

    import psycopg

    src_path = config.DB_PATH
    try:
        src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        print(f"ERROR: no se encontró la base local en {src_path}")
        return 1
    src.row_factory = sqlite3.Row

    movs = [dict(r) for r in src.execute("SELECT * FROM movements")]
    cfgs = [dict(r) for r in src.execute("SELECT key, value FROM config")]
    src.close()

    print(f"Base local: {src_path}")
    print(f"  movimientos: {len(movs)}")
    print(f"  config:      {len(cfgs)}")

    if not movs and not cfgs:
        print("No hay nada para migrar.")
        return 0

    with psycopg.connect(config.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT 1 FROM movements LIMIT 1")
            except psycopg.errors.UndefinedTable:
                print("ERROR: " + TABLES_MSG)
                return 1

            insertados = 0
            for m in movs:
                cur.execute(
                    "INSERT INTO movements"
                    "(id, type, date, effective_date, category, amount, currency, note, created_at) "
                    "VALUES (%(id)s, %(type)s, %(date)s, %(effective_date)s, %(category)s, "
                    "        %(amount)s, %(currency)s, %(note)s, %(created_at)s) "
                    "ON CONFLICT (id) DO NOTHING",
                    {
                        "id": m["id"],
                        "type": m["type"],
                        "date": m["date"],
                        "effective_date": m.get("effective_date") or m["date"],
                        "category": m.get("category") or "",
                        "amount": m["amount"],
                        "currency": (m.get("currency") or "ARS"),
                        "note": m.get("note") or "",
                        "created_at": m.get("created_at") or "",
                    },
                )
                insertados += cur.rowcount

            for c in cfgs:
                cur.execute(
                    "INSERT INTO config(key, value) VALUES (%(key)s, %(value)s) "
                    "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                    c,
                )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM movements")
            total = cur.fetchone()[0]

    print(f"\nListo. Movimientos nuevos insertados: {insertados}")
    print(f"Total de movimientos en la base de producción: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
