"""Integración con Google Gemini.

Tres funciones:
  parse_voice(text)          -> dict con un movimiento sugerido
  transcribe_audio(bytes, mt)-> str con el texto dictado
  parse_attachment(bytes, mt)-> dict con doc_type / card_brand / items[]

Todas devuelven JSON. Si no hay GEMINI_API_KEY configurada se lanza LLMError
con un mensaje claro.
"""
from __future__ import annotations

import base64
import json
from datetime import date

import requests

from . import config

CATS_GASTO = ["Alimentos", "Transporte", "Salud", "Ocio", "Servicios", "Hogar", "Suscripciones", "Otros"]
CATS_IMPUESTO = ["Ganancias", "IIBB", "Monotributo", "ABL/Municipal", "Patente", "Otros"]
CATS_INGRESO_EXTRA = ["Freelance", "Venta", "Bono", "Regalo", "Otros"]

TIMEOUT = 60


class LLMError(Exception):
    """Error al hablar con Gemini o al interpretar su respuesta."""


def _today() -> str:
    return date.today().isoformat()


def _call_gemini(system_prompt: str, parts: list[dict], *, max_tokens: int = 2048) -> str:
    if not config.GEMINI_API_KEY:
        raise LLMError(
            "Falta configurar la clave de Gemini (GEMINI_API_KEY). "
            "Revisá el archivo .env y GUIA.md."
        )

    url = f"{config.GEMINI_ENDPOINT}/{config.GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
        },
    }
    try:
        resp = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": config.GEMINI_API_KEY,
            },
            json=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise LLMError(f"No se pudo conectar con Gemini: {exc}") from exc

    if resp.status_code == 429:
        raise LLMError("Gemini está limitando las consultas (cuota gratuita). Probá de nuevo en un rato.")
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text[:300]
        raise LLMError(f"Gemini devolvió un error ({resp.status_code}): {detail}")

    data = resp.json()
    try:
        candidates = data["candidates"]
        text = "".join(
            p.get("text", "") for p in candidates[0]["content"]["parts"]
        ).strip()
    except (KeyError, IndexError):
        raise LLMError("Gemini no devolvió una respuesta utilizable.")
    if not text:
        raise LLMError("Gemini devolvió una respuesta vacía.")
    return text


def _parse_json(raw: str) -> dict:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[1] if "```" in clean else clean
        if clean.lower().startswith("json"):
            clean = clean[4:]
        clean = clean.strip().rstrip("`").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise LLMError(f"No se entendió la respuesta de Gemini: {exc}") from exc


# --- 1. Texto hablado -> movimiento ---------------------------------------

def parse_voice(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise LLMError("No se recibió texto para interpretar.")

    system_prompt = f"""Convertís una frase hablada en español rioplatense sobre finanzas personales en UN objeto JSON, sin texto adicional, sin markdown, sin backticks. Formato exacto:
{{"type":"gasto_diario|gasto_tarjeta|impuesto|ingreso_sueldo|ingreso_extra","date":"YYYY-MM-DD","category":"string","amount":number,"note":"string breve"}}

Reglas:
- type: "gasto_tarjeta" si menciona tarjeta/crédito/débito con tarjeta; "impuesto" si menciona un impuesto o tasa (ganancias, IIBB, monotributo, ABL, municipal, patente, etc); "ingreso_sueldo" si menciona sueldo/salario/haberes; "ingreso_extra" para otros ingresos (freelance, venta, bono, regalo, changa); si no aplica ninguno de los anteriores y es un gasto, usar "gasto_diario".
- category: para gasto_diario/gasto_tarjeta elegir UNA de {CATS_GASTO}. Para impuesto elegir de {CATS_IMPUESTO}. Para ingreso_extra elegir de {CATS_INGRESO_EXTRA}. Para ingreso_sueldo usar "".
- date: hoy es {_today()}. Si dice "ayer" restar un día. Si no menciona fecha, usar {_today()}. Formato YYYY-MM-DD.
- amount: número en pesos argentinos, sin puntos ni símbolos ni texto (si dice "15 mil" es 15000, si dice "un palo" es 1000000).
- note: 3 a 6 palabras describiendo el movimiento.
Devolvé SOLO el JSON, nada más."""

    raw = _call_gemini(system_prompt, [{"text": text}], max_tokens=300)
    parsed = _parse_json(raw)
    try:
        parsed["amount"] = float(parsed.get("amount") or 0)
    except (TypeError, ValueError):
        parsed["amount"] = 0.0
    if parsed["amount"] <= 0:
        raise LLMError("No se detectó un monto en lo que dijiste.")
    parsed.setdefault("date", _today())
    parsed.setdefault("category", "")
    parsed.setdefault("note", "")
    return parsed


# --- 2. Audio -> texto ---------------------------------------------------

def transcribe_audio(audio_bytes: bytes, mime_type: str) -> str:
    if not audio_bytes:
        raise LLMError("El archivo de audio está vacío.")
    mime_type = (mime_type or "audio/webm").split(";")[0].strip()

    system_prompt = (
        "Transcribís un audio corto en español rioplatense sobre finanzas personales. "
        'Devolvé SOLO un objeto JSON: {"text":"transcripción literal"}. '
        "No agregues comentarios ni interpretación."
    )
    parts = [
        {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(audio_bytes).decode()}},
        {"text": "Transcribí este audio."},
    ]
    raw = _call_gemini(system_prompt, parts, max_tokens=500)
    parsed = _parse_json(raw)
    text = (parsed.get("text") or "").strip()
    if not text:
        raise LLMError("No se pudo transcribir el audio (¿se escuchó algo?).")
    return text


# --- 3. Comprobante (imagen o PDF) -> items ------------------------------

def parse_attachment(file_bytes: bytes, mime_type: str) -> dict:
    if not file_bytes:
        raise LLMError("El archivo está vacío.")
    mime_type = (mime_type or "").split(";")[0].strip()
    is_pdf = mime_type == "application/pdf"
    if not is_pdf and mime_type not in ("image/jpeg", "image/png", "image/webp"):
        raise LLMError("Formato no soportado. Usá una foto (JPG/PNG) o un PDF.")

    today = _today()
    system_prompt = f"""Analizás un comprobante financiero (foto de ticket de compra, o imagen/PDF de un resumen de tarjeta de crédito) en español rioplatense. Devolvé SOLO un objeto JSON, sin texto adicional, sin markdown, sin backticks, con este formato exacto:
{{"doc_type":"ticket|resumen_tarjeta","card_brand":"Visa|Mastercard|","items":[{{"date":"YYYY-MM-DD","merchant":"string","amount":number,"category":"string"}}]}}

Reglas:
- doc_type "ticket": comprobante de una sola compra. "items" tiene un único elemento con el total.
- doc_type "resumen_tarjeta": resumen de tarjeta de crédito con varios consumos. Listá CADA consumo individual como un item separado, no los sumes. Ignorá pagos, impuestos del resumen, intereses y saldos: solo consumos/compras.
- card_brand: "Visa" o "Mastercard" si el documento lo indica claramente, si no dejar "".
- category: para cada item elegir UNA de {CATS_GASTO} según el comercio o rubro.
- date: fecha del consumo en formato YYYY-MM-DD. Si un ítem de un resumen no tiene fecha propia, usar la fecha de cierre del resumen si figura; si no hay ninguna fecha disponible en todo el documento, usar {today}.
- amount: número en pesos, sin puntos de miles ni símbolos. Si el monto está en dólares, convertí NO: dejá el número tal cual y agregá "(USD)" al merchant.
- merchant: nombre del comercio tal como figura, breve (2-4 palabras).
Devolvé SOLO el JSON."""

    mt = "application/pdf" if is_pdf else mime_type
    parts = [
        {"inlineData": {"mimeType": mt, "data": base64.b64encode(file_bytes).decode()}},
        {"text": "Extraé los datos de este comprobante."},
    ]
    raw = _call_gemini(system_prompt, parts, max_tokens=8000)
    parsed = _parse_json(raw)
    items = parsed.get("items") or []
    if not items:
        raise LLMError("No se detectaron consumos en el comprobante.")

    norm_items = []
    for it in items:
        try:
            amount = float(it.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            continue
        norm_items.append(
            {
                "date": it.get("date") or today,
                "merchant": (it.get("merchant") or "").strip(),
                "amount": round(amount, 2),
                "category": (it.get("category") or "Otros").strip() or "Otros",
            }
        )
    if not norm_items:
        raise LLMError("No se detectaron consumos con monto válido en el comprobante.")

    return {
        "doc_type": parsed.get("doc_type") or "ticket",
        "card_brand": parsed.get("card_brand") or "",
        "items": norm_items,
    }
