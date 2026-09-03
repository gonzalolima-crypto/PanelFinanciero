"""Pruebas básicas de la API. No llaman a Gemini (se reemplaza por una función falsa)."""
import os
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("DATA_DIR", tmp)
    monkeypatch.setenv("DB_PATH", os.path.join(tmp, "test.db"))
    monkeypatch.setenv("UPLOAD_DIR", os.path.join(tmp, "uploads"))
    monkeypatch.setenv("APP_PASSWORD", "")  # sin protección para las pruebas
    monkeypatch.setenv("GROQ_API_KEY", "")

    # Recargar config con las env nuevas
    import importlib
    from app import config as app_config
    importlib.reload(app_config)
    from app import db as app_db
    importlib.reload(app_db)
    from app import models, auth, routes, llm
    importlib.reload(models)
    importlib.reload(llm)
    importlib.reload(auth)
    importlib.reload(routes)
    import app as app_pkg
    importlib.reload(app_pkg)

    application = app_pkg.create_app()
    application.config.update(TESTING=True)
    with application.test_client() as c:
        yield c


def test_health(client):
    assert client.get("/health").json == {"status": "ok"}


def test_index_ok_sin_password(client):
    assert client.get("/").status_code == 200


def test_crud_movimientos(client):
    # vacío
    assert client.get("/api/movements").json == []

    # crear
    r = client.post("/api/movements", json={
        "type": "gasto_diario", "date": "2026-08-27",
        "amount": 8000, "category": "Alimentos", "note": "super"
    })
    assert r.status_code == 201
    mid = r.json["id"]

    # listar
    lst = client.get("/api/movements").json
    assert len(lst) == 1 and lst[0]["amount"] == 8000

    # borrar
    assert client.delete(f"/api/movements/{mid}").status_code == 200
    assert client.get("/api/movements").json == []


def test_movimiento_invalido(client):
    r = client.post("/api/movements", json={"type": "x", "date": "2026-08-27", "amount": 10})
    assert r.status_code == 400


def test_effective_date(client):
    # sin effective_date -> igual a date
    r = client.post("/api/movements", json={
        "type": "gasto_diario", "date": "2026-08-10", "amount": 100, "category": "Otros"
    })
    assert r.json["effective_date"] == "2026-08-10"

    # con effective_date (consumo de resumen: compra en julio, vence en agosto)
    r = client.post("/api/movements", json={
        "type": "gasto_tarjeta", "date": "2026-07-15", "amount": 5000,
        "category": "Alimentos", "effective_date": "2026-08-07"
    })
    assert r.status_code == 201
    assert r.json["date"] == "2026-07-15"
    assert r.json["effective_date"] == "2026-08-07"

    lst = client.get("/api/movements").json
    assert all("effective_date" in m for m in lst)


def test_bulk_con_effective_date(client):
    r = client.post("/api/movements/bulk", json={"movements": [
        {"type": "gasto_tarjeta", "date": "2026-06-30", "amount": 1200,
         "category": "Transporte", "effective_date": "2026-08-07"},
        {"type": "gasto_tarjeta", "date": "2026-07-02", "amount": 3400,
         "category": "Ocio", "effective_date": "2026-08-07"},
    ]})
    assert r.status_code == 201
    assert len(r.json["created"]) == 2
    assert {m["effective_date"] for m in r.json["created"]} == {"2026-08-07"}


def test_config(client):
    assert client.get("/api/config").json["goalPct"] == 20
    r = client.put("/api/config", json={"goalPct": 35})
    assert r.json["goalPct"] == 35


def test_voz_sin_apikey_devuelve_502(client):
    r = client.post("/api/voice/parse", json={"text": "gasté 5000 en el super"})
    assert r.status_code == 502
    assert "Groq" in r.json["error"]


def test_parser_consumos_bbva():
    """El parser determinístico extrae los consumos sin llamar a Groq."""
    from app import llm

    texto = "\n".join([
        "Consumos Juan Perez",
        "FECHA", "DESCRIPCIÓN", "NRO. CUPÓN", "PESOS", "DÓLARES",
        "05-Jul-26", "SPOTIFY                  USD        2,99", "834921", "2,99",
        "15-Jul-26", "COTO DIGITAL SUC 215", "005186", "355.776,39",
        "17-Jul-26", "TELEPEAJE PLUS   00034492", "000001", "80,06",
        "30-Jul-26", "COTO DIGITAL DEVOLUCION", "008670", "-2.812,87",
        "TOTAL CONSUMOS DE JUAN PEREZ",
    ])
    items = llm._extract_consumos_regex(texto)
    # 4 líneas de consumo (incluye la devolución negativa de COTO)
    assert len(items) == 4
    coto = next(i for i in items if i["amount"] > 300000)
    assert coto["date"] == "2026-07-15"
    assert coto["category"] == "Compra de Super" and coto["currency"] == "ARS"
    spot = next(i for i in items if "SPOTIFY" in i["merchant"].upper())
    assert spot["currency"] == "USD" and spot["amount"] == 2.99
    assert spot["category"] == "Suscripciones"
    devol = next(i for i in items if i["amount"] < 0)
    assert devol["amount"] == -2812.87

    assert llm._extract_due_date("VENCIMIENTO ACTUAL\n07-Ago-26\n") == "2026-08-07"
    assert llm._extract_due_date("VENCIMIENTO ANTERIOR\n06-Jul-26\nsin actual") == ""


def test_traduccion_sql_postgres(monkeypatch):
    """Con DATABASE_URL de Postgres, las consultas :nombre se traducen a %(nombre)s."""
    import importlib
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    from app import config as cfg
    importlib.reload(cfg)
    from app import db as dbmod
    importlib.reload(dbmod)
    try:
        assert dbmod.IS_PG is True
        assert dbmod._AMOUNT_TYPE == "DOUBLE PRECISION"
        assert dbmod._adapt("DELETE FROM m WHERE id = :id") == "DELETE FROM m WHERE id = %(id)s"
        # los casts :: de postgres no se rompen
        assert dbmod._adapt("SELECT a::text WHERE x = :x") == "SELECT a::text WHERE x = %(x)s"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        importlib.reload(cfg)
        importlib.reload(dbmod)
    assert dbmod.IS_PG is False


def test_reconciliation_extract():
    from app import llm
    raw = "\n".join([
        "SALDO ANTERIOR", "1.378.364,63", "17,16",
        "SU PAGO EN PESOS", "-1.378.364,63",
        "SU PAGO EN USD", "-17,16",
        "TOTAL CONSUMOS DE JUAN PEREZ", "1.746.990,20", "16,55",
        "IIBB PERCEP-CABA 2,00%(   24758,80)", "495,17",
        "IVA RG 4240 21%(   24758,80)", "5.199,34",
        "DB.RG 5617  30% (    24758,80 )", "7.427,64",
        "SALDO ACTUAL", "1.760.112,35", "16,55",
        "Total de cuotas a vencer",
    ])
    r = llm._extract_reconciliation(raw)
    assert r is not None
    assert r["saldo_actual_ars"] == 1760112.35
    assert round(r["cargos_total_ars"], 2) == 13122.15
    assert len(r["cargos"]) == 3
    assert r["consumos_resumen_ars"] == 1746990.20
