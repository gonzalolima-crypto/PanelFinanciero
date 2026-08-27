"""Rutas de la aplicación: la página del panel y la API JSON."""
from flask import Blueprint, jsonify, render_template, request

from . import llm, models
from .auth import login_required, password_required

bp = Blueprint("main", __name__)


@bp.get("/")
@login_required
def index():
    return render_template("index.html", password_required=password_required())


@bp.get("/health")
def health():
    return {"status": "ok"}


# --- Movimientos --------------------------------------------------------

@bp.get("/api/movements")
@login_required
def get_movements():
    return jsonify(models.list_movements())


@bp.post("/api/movements")
@login_required
def create_movement():
    data = request.get_json(silent=True) or {}
    try:
        mv = models.add_movement(
            type=data.get("type", ""),
            date=data.get("date", ""),
            amount=data.get("amount", 0),
            category=data.get("category", ""),
            note=data.get("note", ""),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(mv), 201


@bp.post("/api/movements/bulk")
@login_required
def create_movements_bulk():
    data = request.get_json(silent=True) or {}
    items = data.get("movements") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "No se recibieron movimientos."}), 400
    created, errors = [], []
    for i, it in enumerate(items):
        try:
            created.append(
                models.add_movement(
                    type=it.get("type", ""),
                    date=it.get("date", ""),
                    amount=it.get("amount", 0),
                    category=it.get("category", ""),
                    note=it.get("note", ""),
                )
            )
        except ValueError as exc:
            errors.append({"index": i, "error": str(exc)})
    return jsonify({"created": created, "errors": errors}), 201


@bp.delete("/api/movements/<movement_id>")
@login_required
def remove_movement(movement_id):
    ok = models.delete_movement(movement_id)
    if not ok:
        return jsonify({"error": "No se encontró el movimiento."}), 404
    return jsonify({"deleted": movement_id})


# --- Configuración -----------------------------------------------------

@bp.get("/api/config")
@login_required
def get_config():
    return jsonify(models.get_config())


@bp.put("/api/config")
@login_required
def put_config():
    data = request.get_json(silent=True) or {}
    if "goalPct" in data:
        try:
            v = float(data["goalPct"])
        except (TypeError, ValueError):
            return jsonify({"error": "goalPct inválido"}), 400
        v = max(0.0, min(100.0, v))
        models.set_config("goalPct", v)
    return jsonify(models.get_config())


# --- Gemini: voz y comprobantes ---------------------------------------

@bp.post("/api/voice/parse")
@login_required
def voice_parse():
    data = request.get_json(silent=True) or {}
    try:
        result = llm.parse_voice(data.get("text", ""))
    except llm.LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(result)


@bp.post("/api/voice/transcribe")
@login_required
def voice_transcribe():
    file = request.files.get("audio")
    if file is None:
        return jsonify({"error": "No se recibió audio."}), 400
    try:
        text = llm.transcribe_audio(file.read(), file.mimetype or "audio/webm")
    except llm.LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify({"text": text})


@bp.post("/api/attachment/parse")
@login_required
def attachment_parse():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "No se recibió ningún archivo."}), 400
    try:
        result = llm.parse_attachment(file.read(), file.mimetype or "")
    except llm.LLMError as exc:
        return jsonify({"error": str(exc)}), 502
    result["fileName"] = file.filename or "comprobante"
    return jsonify(result)
