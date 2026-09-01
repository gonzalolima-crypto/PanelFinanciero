"""Integración con Groq (API compatible con OpenAI).

Funciones públicas (no cambian para el resto de la app):
  parse_voice(text)            -> dict con un movimiento sugerido
  transcribe_audio(bytes, mt)  -> str con el texto dictado (Whisper)
  parse_attachment(bytes, mt)  -> dict con doc_type / card_brand / items[]

Cómo funciona cada cosa:
- Voz (texto): modelo de lenguaje de Groq (GROQ_TEXT_MODEL).
- Voz (audio): Whisper de Groq (GROQ_TRANSCRIBE_MODEL).
- Comprobantes en PDF: se extrae el texto con PyMuPDF y lo estructura el
  modelo de lenguaje. Funciona con los resúmenes de tarjeta (Visa/Mastercard)
  y con tickets exportados a PDF.
- Comprobantes como foto (JPG/PNG): sólo si hay un modelo con visión
  configurado en GROQ_VISION_MODEL. Si no, se pide subir el PDF.

Si falta GROQ_API_KEY se lanza LLMError con un mensaje claro.
"""
from __future__ import annotations

import base64
import io
import json
import re
import time
from datetime import date

import fitz  # PyMuPDF
import requests

from . import config

CATS_GASTO = ["Alimentos", "Transporte", "Salud", "Ocio", "Servicios", "Hogar", "Suscripciones", "Otros"]
CATS_IMPUESTO = ["Ganancias", "IIBB", "Monotributo", "ABL/Municipal", "Patente", "Otros"]
CATS_INGRESO_EXTRA = ["Freelance", "Venta", "Bono", "Regalo", "Otros"]

TIMEOUT = 90
MAX_IMAGE_B64 = 3_500_000  # límite de Groq: 4 MB de base64 por imagen
RATE_LIMIT_RETRIES = 2     # reintentos ante error 429 (cuota por minuto)
RATE_LIMIT_MAX_WAIT = 30   # segundos máximos de espera por reintento

# El plan gratuito de Groq limita tokens por minuto (TPM). Groq cuenta
# input + max_tokens de salida contra ese tope. Presupuestamos por debajo.
TPM_BUDGET = 7000
CHARS_PER_TOKEN = 3.3      # estimación conservadora para texto en español con números


def _estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN) + 1


class LLMError(Exception):
    """Error al hablar con Groq o al interpretar su respuesta."""


def _today() -> str:
    return date.today().isoformat()


def _require_key() -> None:
    if not config.GROQ_API_KEY:
        raise LLMError(
            "Falta configurar la clave de Groq (GROQ_API_KEY). "
            "Revisá el archivo .env y GUIA.md."
        )


def _headers() -> dict:
    return {"Authorization": f"Bearer {config.GROQ_API_KEY}"}


def _retry_after_seconds(resp: requests.Response) -> float:
    hdr = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
    if hdr:
        try:
            return float(hdr)
        except ValueError:
            pass
    try:
        msg = resp.json().get("error", {}).get("message", "")
        m = re.search(r"try again in ([\d.]+)s", msg)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return 3.0


def _post(path: str, **kwargs) -> requests.Response:
    """POST con reintento automático ante 429 (límite por minuto de Groq)."""
    url = f"{config.GROQ_BASE_URL}{path}"
    last_resp = None
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            resp = requests.post(url, timeout=TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise LLMError(f"No se pudo conectar con Groq: {exc}") from exc
        if resp.status_code != 429:
            return resp
        last_resp = resp
        if attempt == RATE_LIMIT_RETRIES:
            break
        wait = min(_retry_after_seconds(resp) + 0.5, RATE_LIMIT_MAX_WAIT)
        time.sleep(wait)
    return last_resp


def _handle_http_errors(resp: requests.Response) -> None:
    if resp.status_code == 429:
        raise LLMError(
            "Groq está limitando las consultas (cuota gratuita por minuto). "
            "Esperá un minuto y volvé a intentar."
        )
    if resp.status_code == 401:
        raise LLMError("La clave de Groq no es válida o expiró (revisá GROQ_API_KEY en el .env).")
    if resp.status_code == 404:
        raise LLMError(
            "El modelo configurado no está disponible para tu cuenta de Groq. "
            "Revisá GROQ_TEXT_MODEL / GROQ_VISION_MODEL en el .env."
        )
    if resp.status_code == 413:
        raise LLMError(
            "El comprobante es muy grande para el límite gratuito de Groq. "
            "Probá con un resumen de menos páginas, o cargá los movimientos a mano."
        )
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            detail = resp.text[:300]
        raise LLMError(f"Groq devolvió un error ({resp.status_code}): {detail}")


# --- Llamada base al chat -------------------------------------------

def _chat(messages: list[dict], *, model: str, max_tokens: int = 2048, json_mode: bool = True) -> str:
    _require_key()
    if not model:
        raise LLMError("No hay un modelo configurado para esta operación.")
    payload = {"model": model, "messages": messages, "temperature": 0, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    resp = _post(
        "/chat/completions",
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
    )
    _handle_http_errors(resp)
    try:
        return resp.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise LLMError("Groq no devolvió una respuesta utilizable.")


def _parse_json(raw: str) -> dict:
    clean = (raw or "").strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[1] if clean.count("```") >= 2 else clean.strip("`")
        if clean.lower().startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    if not clean.startswith("{"):
        i = clean.find("{")
        if i != -1:
            clean = clean[i:]
    if not clean.endswith("}"):
        j = clean.rfind("}")
        if j != -1:
            clean = clean[: j + 1]
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise LLMError(f"No se entendió la respuesta del modelo: {exc}") from exc


# --- 1. Texto hablado -> movimiento -------------------------------

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

    raw = _chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=config.GROQ_TEXT_MODEL,
        max_tokens=300,
    )
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


# --- 2. Audio -> texto (Whisper) --------------------------------

def transcribe_audio(audio_bytes: bytes, mime_type: str) -> str:
    _require_key()
    if not audio_bytes:
        raise LLMError("El archivo de audio está vacío.")
    mime_type = (mime_type or "audio/webm").split(";")[0].strip()
    ext = mime_type.split("/")[-1] or "webm"
    ext = {"mpeg": "mp3", "x-m4a": "m4a", "x-wav": "wav", "vnd.wave": "wav"}.get(ext, ext)

    resp = _post(
        "/audio/transcriptions",
        headers=_headers(),
        files={"file": (f"audio.{ext}", io.BytesIO(audio_bytes), mime_type)},
        data={
            "model": config.GROQ_TRANSCRIBE_MODEL,
            "language": "es",
            "response_format": "json",
            "temperature": "0",
        },
    )
    _handle_http_errors(resp)
    try:
        text = (resp.json().get("text") or "").strip()
    except Exception:
        raise LLMError("Groq no devolvió una transcripción utilizable.")
    if not text:
        raise LLMError("No se pudo transcribir el audio (¿se escuchó algo?).")
    return text


# --- 3. Comprobante -> items ------------------------------------

_ATTACH_RULES = f"""Devolvé SOLO un objeto JSON válido (sin texto adicional, sin markdown, sin backticks):
{{"doc_type":"ticket|resumen_tarjeta","card_brand":"Visa|Mastercard|Amex|","due_date":"YYYY-MM-DD|","items":[{{"date":"YYYY-MM-DD","merchant":"string","amount":number,"category":"string"}}]}}

Reglas:
- doc_type "ticket": comprobante de una sola compra -> "items" tiene un único elemento con el total.
- doc_type "resumen_tarjeta": resumen de tarjeta con varios consumos -> listá CADA consumo como un item separado, NO los sumes.
- Incluí únicamente CONSUMOS / COMPRAS reales (de cualquier titular de la cuenta).
  EXCLUÍ: pagos ("SU PAGO EN PESOS/USD"), ajustes, percepciones e impuestos del resumen
  (IIBB, IVA RG, DB.RG, sellado), intereses, punitorios, "cuotas a vencer" y saldos.
- card_brand: "Visa", "Mastercard" o "Amex" si el documento lo indica claramente; si no, "".
- due_date: SOLO para doc_type "resumen_tarjeta". Es la fecha de "VENCIMIENTO ACTUAL"
  (o "Fecha de vencimiento" / "Vencimiento del pago") de ESTE resumen, en formato YYYY-MM-DD.
  NO uses "vencimiento anterior" ni "próximo vencimiento". Si no figura, dejá "".
- category: elegí UNA de {CATS_GASTO} según el comercio o rubro.
- date: formato YYYY-MM-DD. El resumen usa formatos como "28-Jul-26" (= 2026-07-28).
  Si un consumo no tiene fecha propia, usá la fecha de cierre del resumen.
- amount: número en pesos, sin separador de miles ni símbolos (ej: 220582.37).
  Si el consumo está expresado en dólares (USD/U$S), dejá el número tal cual y agregá " (USD)" al final del merchant.
- merchant: nombre del comercio tal como figura, breve (2-4 palabras).
"""


def _extract_due_date(raw: str) -> str:
    """Busca la fecha de 'VENCIMIENTO ACTUAL' en el texto crudo del resumen."""
    date_pat = r"([0-3]?\d[-/](?:[A-Za-zÁÉÍÓÚáéíóú]{3,}|\d{1,2})[-/]\d{2,4})"
    patterns = [
        r"VENCIMIENTO\s+ACTUAL\s{0,10}" + date_pat,
        r"(?:fecha\s+(?:de\s+|l[ií]mite\s+de\s+)?)?"
        r"(?:vencimiento(?:\s+del\s+pago)?|pago\s+hasta(?:\s+el)?|payment\s+due\s+date)"
        r"\s{0,3}[:\-]?\s{0,10}" + date_pat,
    ]
    for pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            d = _normalize_date(m.group(1))
            if d:
                return d
    return ""


class _PdfContent:
    __slots__ = ("llm_text", "consumos", "brand", "due_date")

    def __init__(self, llm_text: str, consumos: str, brand: str, due_date: str):
        self.llm_text = llm_text      # texto a mandar al modelo (fallback)
        self.consumos = consumos      # solo los bloques de consumos (para el parser regex)
        self.brand = brand
        self.due_date = due_date


def _pdf_text(file_bytes: bytes) -> "_PdfContent":
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise LLMError(f"No se pudo abrir el PDF: {exc}") from exc
    try:
        n = min(doc.page_count, config.PDF_MAX_PAGES)
        if n == 0:
            raise LLMError("El PDF no tiene páginas.")
        raw = "\n".join(doc.load_page(i).get_text("text") for i in range(n))
    finally:
        doc.close()

    if len(raw.strip()) < 20:
        raise LLMError(
            "El PDF no tiene texto seleccionable (parece escaneado). "
            "Probá con el PDF original del banco, o cargá los movimientos a mano."
        )

    brand = ""
    low = raw.lower()
    if "mastercard" in low:
        brand = "Mastercard"
    elif re.search(r"\bvisa\b", low):
        brand = "Visa"
    elif "american express" in low or re.search(r"\bamex\b", low):
        brand = "Amex"

    due_date = _extract_due_date(raw)

    noise = re.compile(
        r"^\s*(Sobre \(\d+\)|Banco BBVA Argentina|.*Página \d+ de \d+|"
        r"OCASA - R\.N\.P\.S\.P|URBOES|1/1 \d+|.*DIGITAL\s*$)",
        re.IGNORECASE,
    )
    lines = [ln for ln in raw.splitlines() if ln.strip() and not noise.match(ln)]
    consumos = _focus_statement("\n".join(lines))

    llm_text = consumos
    # Si el regex NO encontró el vencimiento (otro banco / formato raro),
    # anteponemos un encabezado acotado con las líneas de fechas/vencimiento
    # para que el modelo lo intente. Si el regex ya lo tiene, no hace falta.
    if not due_date:
        keep = re.compile(
            r"(vencimiento|cierre|fecha\s+(de\s+)?pago|pago\s+m[ií]nimo|"
            r"payment\s+due|closing\s+date|\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4})",
            re.IGNORECASE,
        )
        header = [ln for ln in lines[:70] if keep.search(ln)][:20]
        if header:
            llm_text = "DATOS DEL RESUMEN:\n" + "\n".join(header) + "\n\nCONSUMOS:\n" + consumos

    return _PdfContent(llm_text, consumos, brand, due_date)


def _focus_statement(text: str) -> str:
    """Deja sólo las secciones de consumos de un resumen de tarjeta.

    Un resumen BBVA tiene bloques 'Consumos <Titular>' ... 'TOTAL CONSUMOS DE ...'.
    El resto (saldos, límites, tasas, pagos, impuestos del resumen, cuotas a
    vencer) no aporta consumos y sólo gasta tokens.
    """
    lines = text.splitlines()
    start_re = re.compile(r"^\s*Consumos\s+.+", re.IGNORECASE)
    end_re = re.compile(r"^\s*TOTAL CONSUMOS DE\b", re.IGNORECASE)

    blocks, keeping = [], False
    for ln in lines:
        if start_re.match(ln):
            keeping = True
            blocks.append(ln)
            continue
        if keeping:
            blocks.append(ln)
            if end_re.match(ln):
                keeping = False

    focused = "\n".join(blocks).strip()
    # Si no encontramos el patrón (ticket suelto, otro banco), usar el texto
    # completo salvo que sea enorme.
    if len(focused) < 40:
        return text if len(text) <= 9000 else text[:9000]
    return focused


# --- Parser determinístico de consumos (formato BBVA Visa/Mastercard) ---

_CAT_KEYWORDS = [
    ("Alimentos", r"COTO|CARREFOUR|JUMBO|\bDIA\b|DISCO|VEA |LA ANONIMA|LA ANÓNIMA|CHANGOMAS|"
                  r"WALMART|MAKRO|VITAL|MAXICONSUMO|ALMACEN|VERDULER|CARNICER|PANADER|"
                  r"KIOSCO|RESTO|RESTAURANT|MC DONALD|MCDONALD|BURGER|STARBUCKS|CAFE|BAR "),
    ("Transporte", r"YPF|SHELL|AXION|PUMA ENERGY|GNC|ESTACION|AUTOPISTA|TELEPEAJE|PEAJE|AUBASA|"
                   r"AUSA|CAMINOS|SUBE|MERPAGO\*?SUBE|UBER|CABIFY|DIDI|BEAT|REMIS|TAXI|"
                   r"AVIS|HERTZ|LOCALIZA|RENT.?A.?CAR|AEROLINEAS|LATAM|FLYBONDI|JETSMART|"
                   r"ESTACIONAMIENTO|PARKING|CVSA|VTV"),
    ("Suscripciones", r"NETFLIX|SPOTIFY|DISNEY|HBO|MAX\b|PARAMOUNT|PRIME VIDEO|AMAZON PRIME|"
                      r"YOUTUBE|APPLE\.COM|APPLE COM|GOOGLE \*|GOOGLE\*|ITUNES|PLAYSTATION|"
                      r"XBOX|NINTENDO|CANVA|NOTION|CHATGPT|OPENAI|DROPBOX|MERCADO LIBRE\+|"
                      r"MELI\+|CLARO VIDEO|FLOW\b|PARAMOUNT"),
    ("Servicios", r"TELECENTRO|FIBERTEL|CABLEVISION|CABLEVISIÓN|MOVISTAR|CLARO|PERSONAL|TUENTI|"
                  r"IPLAN|GIGARED|EDENOR|EDESUR|EDEA|METROGAS|NATURGY|CAMUZZI|AYSA|ABL|RENTAS|"
                  r"AGIP|ARBA|MUNICIPAL|SEGURO|SEGUROS|CAJA SEG|LA CAJA|SANCOR SEG|"
                  r"PREVENCION|GALENO|EXPENSAS|CONSORCIO|PAGOS360|RAPIPAGO|PAGO FACIL|"
                  r"PAGOFACIL|BApro|PROVINCIA NET"),
    ("Salud", r"FARMACIA|FARMACITY|FARMACIAS|DR AHORRO|DEL DR|PHARMACY|CVS|HOSPITAL|SANATORIO|"
              r"CLINICA|CLÍNICA|LABORATOR|DENTAL|ODONTO|OPTICA|ÓPTICA|OSDE|SWISS MEDICAL|"
              r"MEDICUS|GALENO|OMINT|MEDIFE|HOMEOPAT"),
    ("Hogar", r"ARREDO|EASY|SODIMAC|SODIMCO|FALABELLA|MERCADO LIBRE|MERCADOLIBRE|MERPAGO\*?"
              r"(?:DILUCE|LAMAYOR)|BAZAR|FERRETER|PINTURER|SANITARIOS|MUEBLES|MOVISTAR HOGAR|"
              r"DECO|BLANQUER|RITZ|LA CARDEUSE|SIMMONS|PIERO"),
    ("Ocio", r"CINE|CINEMA|HOYTS|CINEMARK|SHOWCASE|TEATRO|SPOTIFY|GARBARINO|FRAVEGA|"
             r"MUSIMUNDO|DUTY FREE|CLUB|GIMNASIO|GYM|SPORTCLUB|MEGATLON|PADEL|"
             r"CANCHA|BOWLING|PARQUE|KANSAS|KENTUCKY|LA MISION|HELAD"),
]

_CONSUMO_DATE = re.compile(r"^\s*(\d{1,2}-[A-Za-zÁÉÍÓÚáéíóú]{3,}-\d{2,4})\s*$")
_CONSUMO_AMOUNT = re.compile(r"^\s*(-?\$?\s?[\d.]{1,15},\d{2})\s*$")
_CONSUMO_CUPON = re.compile(r"^\s*\d{3,12}\s*$")
_SECTION_LINE = re.compile(r"^\s*(TOTAL CONSUMOS DE|Consumos\s+\S|FECHA|DESCRIPCI|NRO\.|PESOS|D[ÓO]LARES)", re.IGNORECASE)


def _categorize(merchant: str) -> str:
    up = merchant.upper()
    for cat, pat in _CAT_KEYWORDS:
        if re.search(pat, up):
            return cat
    return "Otros"


def _amount_to_float(s: str) -> float:
    s = s.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _clean_merchant(desc: str) -> str:
    m = re.split(r"\s{2,}", desc.strip(), maxsplit=1)[0]           # corta en doble espacio
    m = re.sub(r"\b(USD|U\$S)\b.*$", "", m, flags=re.IGNORECASE)   # saca "USD 2,99"
    m = re.sub(r"\bC\.\d{2}/\d{2}\b.*$", "", m)                    # saca cuota "C.03/06"
    m = re.sub(r"\s+\S*\d{4,}\S*\s*$", "", m)                      # saca códigos de referencia al final
    m = re.sub(r"[*]+", " ", m).strip(" -*")
    return re.sub(r"\s{2,}", " ", m).strip()[:40]


def _extract_consumos_regex(consumos_text: str) -> list[dict]:
    """Extrae los consumos de un resumen BBVA de forma determinística
    (sin depender del modelo). Devuelve items sin categoría normalizada."""
    lines = consumos_text.splitlines()
    items: list[dict] = []
    i, n = 0, len(lines)
    while i < n:
        md = _CONSUMO_DATE.match(lines[i])
        if not md:
            i += 1
            continue
        date = _normalize_date(md.group(1))
        j = i + 1
        # descripción: primera línea siguiente que no sea monto/cupón/sección
        desc = ""
        while j < n:
            s = lines[j].strip()
            if not s or _SECTION_LINE.match(s) or _CONSUMO_DATE.match(lines[j]):
                break
            if _CONSUMO_AMOUNT.match(lines[j]) or _CONSUMO_CUPON.match(lines[j]):
                j += 1
                continue
            desc = s
            j += 1
            break
        # montos: las siguientes líneas que sean monto (saltando cupón)
        amounts = []
        while j < n:
            s = lines[j].strip()
            if _CONSUMO_CUPON.match(s):
                j += 1
                continue
            if _CONSUMO_AMOUNT.match(s):
                amounts.append(s)
                j += 1
                continue
            break
        if desc and amounts:
            is_usd = bool(re.search(r"\b(USD|U\$S)\b", desc, re.IGNORECASE))
            value = _amount_to_float(amounts[0])
            merchant = _clean_merchant(desc)
            if is_usd and "(USD)" not in merchant:
                merchant = (merchant + " (USD)").strip()
            items.append({
                "date": date or _today(),
                "merchant": merchant,
                "amount": value,
                "category": _categorize(merchant),
            })
        i = max(j, i + 1)
    return items


def _image_data_url(file_bytes: bytes, mime_type: str) -> str:
    filetype = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(mime_type)
    if not filetype:
        raise LLMError("Formato de imagen no soportado. Usá JPG, PNG o PDF.")
    try:
        doc = fitz.open(stream=file_bytes, filetype=filetype)
        page = doc.load_page(0)
        longest = max(page.rect.width, page.rect.height) or 1.0
        zoom = min(2.0, 1800.0 / longest)
        quality = 82
        for _ in range(6):
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            data = pix.tobytes(output="jpeg", jpg_quality=quality)
            b64 = base64.b64encode(data).decode()
            if len(b64) <= MAX_IMAGE_B64:
                doc.close()
                return f"data:image/jpeg;base64,{b64}"
            if quality > 45:
                quality -= 15
            else:
                zoom *= 0.75
        doc.close()
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError(f"No se pudo procesar la imagen: {exc}") from exc
    raise LLMError("La imagen es demasiado grande incluso después de comprimirla.")


def _normalize_result(parsed: dict) -> dict:
    today = _today()
    raw_items = parsed.get("items") or []
    norm, seen = [], set()
    for it in raw_items:
        try:
            amount = float(it.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            continue
        merchant = (it.get("merchant") or "").strip()
        d = _normalize_date(it.get("date")) or today
        key = (d, merchant.lower(), round(amount, 2))
        if key in seen:
            continue
        seen.add(key)
        norm.append({
            "date": d,
            "merchant": merchant,
            "amount": round(amount, 2),
            "category": (it.get("category") or "Otros").strip() or "Otros",
        })
    if not norm:
        raise LLMError("No se detectaron consumos con monto válido en el comprobante.")
    return {
        "doc_type": parsed.get("doc_type") or "ticket",
        "card_brand": parsed.get("card_brand") or "",
        "due_date": _normalize_date(parsed.get("due_date")),
        "items": norm,
    }


_MONTHS = {m: i for i, m in enumerate(
    ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"], start=1)}
_MONTHS.update({"jan": 1, "apr": 4, "aug": 8, "dec": 12})


def _normalize_date(value) -> str:
    if not value:
        return ""
    s = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})[-/ ]([A-Za-zÁÉÍÓÚáéíóú]{3,})[-/ ](\d{2,4})", s)
    if m:
        day, mon, year = m.groups()
        mon = _MONTHS.get(mon[:3].lower())
        if mon:
            year = int(year)
            year += 2000 if year < 100 else 0
            return f"{year:04d}-{mon:02d}-{int(day):02d}"
    m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", s)
    if m:
        day, mon, year = (int(x) for x in m.groups())
        year += 2000 if year < 100 else 0
        return f"{year:04d}-{mon:02d}-{day:02d}"
    return ""


def _statement_call(text: str) -> dict:
    system_tokens = _estimate_tokens(_ATTACH_RULES)
    input_tokens = _estimate_tokens(text) + system_tokens + 30
    out_budget = TPM_BUDGET - input_tokens
    if out_budget < 500:
        raise LLMError(
            "El comprobante es muy grande para el límite gratuito de Groq. "
            "Probá con un resumen de menos páginas, o cargá los movimientos a mano."
        )
    raw = _chat(
        [
            {"role": "system", "content": _ATTACH_RULES},
            {"role": "user", "content": "Texto extraído del comprobante:\n\n" + text},
        ],
        model=config.GROQ_TEXT_MODEL,
        max_tokens=min(4000, out_budget),
    )
    return _parse_json(raw)


def _split_statement(text: str) -> list[str]:
    """Parte un resumen en trozos (por bloque 'Consumos <Titular>') que quepan
    en el presupuesto de tokens."""
    parts = re.split(r"(?im)^(?=\s*Consumos\s+\S)", text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return [text]
    budget_chars = int((TPM_BUDGET - 1500 - _estimate_tokens(_ATTACH_RULES)) * CHARS_PER_TOKEN)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > budget_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks


def _parse_statement_text(text: str, brand_hint: str = "", due_date_hint: str = "") -> dict:
    if _estimate_tokens(text) + _estimate_tokens(_ATTACH_RULES) + 1000 <= TPM_BUDGET:
        result = _statement_call(text)
    else:
        result = {"doc_type": "resumen_tarjeta", "card_brand": "", "due_date": "", "items": []}
        for i, chunk in enumerate(_split_statement(text)):
            part = _statement_call(chunk)
            if i == 0:
                result["doc_type"] = part.get("doc_type") or "resumen_tarjeta"
                result["card_brand"] = part.get("card_brand") or ""
                result["due_date"] = part.get("due_date") or ""
            result["items"].extend(part.get("items") or [])
    if not result.get("card_brand") and brand_hint:
        result["card_brand"] = brand_hint
    # El regex sobre el texto crudo es más confiable que el modelo: tiene prioridad.
    if due_date_hint:
        result["due_date"] = due_date_hint
    return result


def parse_attachment(file_bytes: bytes, mime_type: str) -> dict:
    if not file_bytes:
        raise LLMError("El archivo está vacío.")
    mime_type = (mime_type or "").split(";")[0].strip().lower()

    if mime_type == "application/pdf":
        pdf = _pdf_text(file_bytes)

        # 1) Parser determinístico (formato BBVA). Es fiel y no gasta cuota.
        regex_items = _extract_consumos_regex(pdf.consumos)
        if len(regex_items) >= 2:
            parsed = {
                "doc_type": "resumen_tarjeta",
                "card_brand": pdf.brand,
                "due_date": pdf.due_date,
                "items": regex_items,
            }
        else:
            # 2) Fallback: el modelo (otros bancos / tickets sueltos).
            parsed = _parse_statement_text(pdf.llm_text, pdf.brand, pdf.due_date)

        result = _normalize_result(parsed)
        if result.get("doc_type") != "resumen_tarjeta":
            result["due_date"] = ""  # un ticket suelto no se imputa por vencimiento
        return result

    # Imagen: sólo si hay un modelo con visión configurado
    if mime_type in ("image/jpeg", "image/png", "image/webp"):
        if not config.GROQ_VISION_MODEL:
            raise LLMError(
                "Con la configuración actual sólo puedo leer comprobantes en PDF. "
                "Guardá el ticket como PDF (o sacale una captura y \"Imprimir a PDF\"), "
                "o cargá el movimiento a mano."
            )
        url = _image_data_url(file_bytes, mime_type)
        raw = _chat(
            [
                {"role": "system", "content": _ATTACH_RULES},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extraé los datos de este comprobante."},
                    {"type": "image_url", "image_url": {"url": url}},
                ]},
            ],
            model=config.GROQ_VISION_MODEL,
            max_tokens=6000,
        )
        return _normalize_result(_parse_json(raw))

    raise LLMError("Formato no soportado. Usá un PDF, o una foto JPG/PNG.")
