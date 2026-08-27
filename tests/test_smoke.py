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
    monkeypatch.setenv("GEMINI_API_KEY", "")

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


def test_config(client):
    assert client.get("/api/config").json["goalPct"] == 20
    r = client.put("/api/config", json={"goalPct": 35})
    assert r.json["goalPct"] == 35


def test_voz_sin_apikey_devuelve_502(client):
    r = client.post("/api/voice/parse", json={"text": "gasté 5000 en el super"})
    assert r.status_code == 502
    assert "Gemini" in r.json["error"]
