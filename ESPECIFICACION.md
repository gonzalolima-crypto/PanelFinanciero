# Especificación — Panel Financiero

Documento de desarrollo guiado por especificaciones (SDD). Refleja lo acordado
en la reunión del 27/08/2026 (`tarea.md`) y las respuestas posteriores.

> Cambio 01/09/2026 (a): el proveedor de IA pasó de Google Gemini a **Groq**
> (clave provista por el usuario). Ver sección 4.
>
> Cambio 01/09/2026 (b): los consumos de un **resumen de tarjeta** se imputan al
> mes de la **fecha de vencimiento** (VENCIMIENTO ACTUAL), no al mes de cada
> compra. Nuevo campo `movements.effective_date`. Ver secciones 3.1 y 4.
>
> Cambio 02/09/2026: **doble moneda** (`movements.currency` ARS/USD) con resumen
> paralelo $ y US$; los consumos en dólares se cargan literales en USD; las
> devoluciones se cargan negativas; y al subir un resumen se muestra un panel de
> **reconciliación** con las percepciones/impuestos del resumen (que NO se cargan
> como movimiento) para cuadrar contra el SALDO ACTUAL.

## 1. Objetivo

Convertir el prototipo `panel-financiero.html` (maqueta HTML con almacenamiento
del navegador y llamadas directas a una API de IA) en una aplicación web
funcional, personal, con backend propio y base de datos, publicable en internet
con acceso protegido.

## 2. Alcance de esta versión (v1)

Se mantiene **exactamente** el modelo funcional del prototipo:

- Tipos de movimiento: `gasto_diario`, `gasto_tarjeta`, `impuesto`,
  `ingreso_sueldo`, `ingreso_extra`.
- Categorías por tipo (idénticas al prototipo).
- Objetivo de ahorro configurable (% del ingreso), por defecto 20%.
- Resumen mensual tipo recibo + selector de mes.
- Los mismos 6 gráficos (Chart.js): gasto diario, gasto tarjeta, ingresos
  apilados, impuestos, ahorro vs objetivo, distribución por categoría.
- Tabla de movimientos del mes con borrado por fila.

Agregados respecto del prototipo:

- Backend **Flask + SQLite3** (persistencia real, multi-dispositivo).
- **Autenticación por contraseña única** (sesión con cookie firmada).
- Carga por voz con **dos vías**: dictado en vivo (Web Speech API del navegador)
  y **subida de audio** transcripta en el servidor con Whisper (Groq).
- Interpretación de voz y de comprobantes movida al backend (la API key queda
  del lado del servidor, nunca en el navegador).
- Lectura de comprobantes **en PDF** (resúmenes de tarjeta y tickets): el texto
  se extrae con PyMuPDF y lo estructura el modelo de lenguaje.

Fuera de alcance en v1 (se puede agregar después, es barato):

- Importación de CSV/Excel de banco en lote.
- Múltiples usuarios / cuentas separadas.
- Edición de un movimiento existente (hoy: borrar y volver a cargar).
- Lectura de comprobantes como **foto JPG/PNG**: requiere un modelo con visión.
  El código ya lo soporta (`GROQ_VISION_MODEL`), pero la cuenta de Groq actual
  no tiene uno habilitado. Mientras tanto: convertir la foto a PDF.
- Adjuntar TXT como comprobante.

## 3. Arquitectura

```
Navegador (HTML + JS + Chart.js)
        │  fetch /api/*
        ▼
Flask (app/)  ──►  SQLite3 (data/panel.db)
        │
        │   PDF ─► PyMuPDF (extrae texto)
        │
        └──►  Groq API (api.groq.com, compatible con OpenAI)
                 · parse_voice      : texto hablado        → movimiento   (GROQ_TEXT_MODEL)
                 · transcribe_audio : audio                → texto        (GROQ_TRANSCRIBE_MODEL, Whisper)
                 · parse_attachment : texto del PDF        → consumos     (GROQ_TEXT_MODEL)
                                      (foto JPG/PNG        → consumos     si hay GROQ_VISION_MODEL)
```

- **Servidor de desarrollo**: `python run.py` (Flask, puerto 8000).
- **Servidor de producción**: `gunicorn wsgi:app` dentro de un contenedor
  Docker, desplegado en Fly.io con un volumen persistente montado en `/data`.

### 3.1 Modelo de datos (SQLite)

```sql
movements(
  id TEXT PK, type TEXT,
  date TEXT (YYYY-MM-DD),            -- fecha real de la compra / del movimiento
  effective_date TEXT (YYYY-MM-DD),  -- fecha con la que se imputa a un mes
  category TEXT,
  amount REAL,                       -- puede ser negativo (reintegro / devolución en un gasto)
  currency TEXT DEFAULT 'ARS',       -- 'ARS' | 'USD'
  note TEXT, created_at TEXT
)
config(key TEXT PK, value TEXT)   -- hoy: goalPct
```

- `effective_date` = `date` para casi todo. Para los consumos de un resumen de
  tarjeta es la **fecha de vencimiento** del resumen. Todos los agrupamientos por
  mes (recibo, gráficos, selector de mes) usan `effective_date`; la tabla de
  movimientos muestra `date`.
- `currency`: los sumarios de pesos y de dólares se calculan por separado
  (`sumBy(list, type, currency)` en el frontend). Los gráficos son solo ARS.
- `amount` negativo: sólo para gastos (reintegro); un ingreso negativo es error.
- Migración automática para bases previas (`_migrate()` en `app/db.py`, backfill
  `effective_date = date`, `currency = 'ARS'`).

### 3.2 API HTTP

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Página del panel (requiere sesión) |
| GET/POST | `/login`, POST `/logout` | Contraseña única |
| GET | `/health` | Chequeo de salud (para Fly) |
| GET | `/api/movements` | Lista todos los movimientos |
| POST | `/api/movements` | Alta de un movimiento |
| POST | `/api/movements/bulk` | Alta de varios (confirmar comprobante) |
| DELETE | `/api/movements/<id>` | Baja |
| GET/PUT | `/api/config` | Leer / actualizar configuración (`goalPct`) |
| POST | `/api/voice/parse` | `{text}` → movimiento sugerido (Groq) |
| POST | `/api/voice/transcribe` | `audio` (multipart) → `{text}` (Whisper/Groq) |
| POST | `/api/attachment/parse` | `file` (multipart, PDF o imagen) → consumos (Groq) |

Todas las rutas `/api/*` responden **401** si no hay sesión y la contraseña
está configurada.

### 3.3 Configuración (variables de entorno)

| Variable | Default | Uso |
|---|---|---|
| `APP_PASSWORD` | *(vacío)* | Contraseña de acceso. Vacío = sin protección (solo local). |
| `SECRET_KEY` | `dev-inseguro-cambiar` | Firma de cookies de sesión. |
| `GROQ_API_KEY` | *(vacío)* | Clave de Groq. Sin ella, voz y comprobantes fallan con 502. |
| `GROQ_TEXT_MODEL` | `openai/gpt-oss-120b` | Modelo para voz y para estructurar el texto de los PDF. |
| `GROQ_TRANSCRIBE_MODEL` | `whisper-large-v3-turbo` | Modelo para transcribir audios. |
| `GROQ_VISION_MODEL` | *(vacío)* | Modelo con visión para fotos JPG/PNG. Vacío = comprobantes solo en PDF. |
| `DB_PATH` | `./data/panel.db` | Ruta del archivo SQLite. En Fly: `/data/panel.db`. |
| `UPLOAD_DIR` | `./data/uploads` | Carpeta de comprobantes subidos. |
| `PDF_MAX_PAGES` | `8` | Máximo de páginas de un PDF que se procesan. |
| `MAX_CONTENT_MB` | `25` | Límite de tamaño de subida. |
| `PORT` | `8000` (local) / `8080` (Docker) | Puerto. |

## 4. Decisiones y justificación

| Decisión | Motivo |
|---|---|
| Flask + SQLite3 | Acordado en la reunión. Baja complejidad, una sola persona lo usa. |
| Groq (nivel gratuito) | Clave provista por el usuario. API compatible con OpenAI. Incluye Whisper para audio. Proveedor/modelo intercambiable por variables de entorno. |
| Comprobantes: extraer texto del PDF + estructurar con LLM | La cuenta de Groq del usuario no tiene modelo con visión. Los resúmenes del banco son PDF con texto seleccionable, así que la extracción con PyMuPDF es 100 % fiel y además usa menos tokens que enviar imágenes. |
| "Focalizar" el texto del resumen antes de mandarlo | El plan gratuito de Groq tiene un límite bajo de tokens por minuto (~8000, e incluye el `max_tokens` de salida). `_focus_statement()` deja sólo los bloques "Consumos … / TOTAL CONSUMOS DE …" (de ~13 KB a <1 KB). Si aún así no entra, `_split_statement()` lo parte por titular y hace varias llamadas. |
| Parser determinístico de consumos (`_extract_consumos_regex`) | El formato BBVA Visa/Mastercard es regular (fecha / descripción / cupón / monto). Se extraen los consumos con regex + categorización por palabras clave (`_categorize`). Rápido, exacto, sin cuota, y **sin la inconsistencia del LLM** (que a veces devolvía 15 de 27 ítems). El modelo queda solo de fallback para PDFs que el regex no reconoce (otros bancos, tickets sueltos). |
| Fecha de vencimiento: regex primero, LLM de respaldo | `_extract_due_date()` busca "VENCIMIENTO ACTUAL" en el texto crudo. Si falla, se le pasa al modelo un encabezado acotado y devuelve `due_date` en el JSON. Si ninguno la encuentra, el frontend la pide al usuario. |
| Reconciliación (`_extract_reconciliation`) | Parsea el "resumen de cuenta" del PDF (SALDO ANTERIOR → SALDO ACTUAL): pagos, total de consumos, percepciones/impuestos, saldo. `_build_reconciliation_view()` compara lo que carga el panel (neto de devoluciones, por moneda) contra el total de consumos del resumen y muestra las percepciones aparte. Los cargos del resumen NO se cargan como movimientos (decisión del usuario). |
| Detección de moneda del consumo | Sólo el token "USD" / "U$S" (a veces pegado al cupón: "…285USD"). NO se usa "DÓLAR/DOLARES" porque aparece en nombres de comercios ("DUTY FREE SHOP DOLARES") que se pagan en pesos. |
| Deducir tipo de archivo por extensión | Algunos navegadores/Windows no informan el MIME al subir; el backend lo deduce de la extensión del nombre. |
| `GROQ_VISION_MODEL` opcional | Si en el futuro se habilita un modelo con visión, basta setear la variable y las fotos JPG/PNG funcionan sin cambios de código. |
| API key en el backend | El prototipo la exponía en el navegador. Riesgo de robo de clave y de cuota. |
| Contraseña única (no login por usuario) | Uso personal. Suficiente para proteger un link público. |
| Fly.io | Nivel gratuito con **disco persistente** (SQLite sobrevive a los deploys) y salida a internet permitida (necesaria para llamar a Groq). Render gratuito borra el disco; PythonAnywhere gratuito bloquea las llamadas salientes. |
| Chart.js servido localmente (`app/static/vendor/`) | La app funciona sin depender de un CDN. |
| Voz: dictado en vivo + audio al servidor | El dictado en vivo (Web Speech API) es gratis pero solo Chrome de escritorio/Android. La subida de audio (Whisper) cubre iPhone/Safari. |
| Reintento ante 429 | El plan gratuito de Groq limita tokens por minuto; `app/llm.py` reintenta hasta 2 veces respetando `Retry-After`. |

## 5. Plan de trabajo

1. **Local primero.** Se entrega la app corriendo en la máquina del usuario
   (`iniciar.bat`). El usuario prueba: traducción de voz, adjuntar los PDF de
   `Comprobantes/`, estabilidad, y devuelve observaciones.
2. **Ajustes** según feedback (categorías, textos, prompts, etc.).
3. **Publicación.** Con el visto bueno: `git push` al repositorio + `fly deploy`
   siguiendo `GUIA.md` sección 4.

## 6. Pruebas

- Automáticas: `tests/test_smoke.py` (pytest) — CRUD de movimientos,
  configuración, autenticación y manejo de error cuando falta la API key.
  No consumen cuota de Groq.
- Verificado contra la API real de Groq (01/09/2026):
  - `parse_voice` con 4 frases → tipo, monto, fecha ("ayer", "950 lucas"),
    categoría y nota correctos.
  - `parse_attachment` con `Comprobantes/Resumen Visa Pago Agosto.pdf`
    (27 consumos) y `Resumen Mastercard Pago Agosto.pdf` (9 consumos):
    fechas convertidas, dólares marcados "(USD)", pagos/impuestos excluidos.
- Manuales (a cargo del usuario en local):
  - [ ] Dictar 3-4 movimientos por voz y verificar el formulario autocompletado.
  - [ ] Grabar un audio ("subir un audio grabado") y verificar la transcripción.
  - [ ] Subir los dos PDF de `Comprobantes/` y revisar la agrupación.
  - [ ] Convertir una foto de ticket a PDF y adjuntarla.
  - [ ] Cerrar y reabrir la app; confirmar que los datos siguen ahí.
  - [ ] Probar desde el celular (misma red, `http://IP-de-la-PC:8000`).

## 7. Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| Límite de tokens por minuto de Groq (429) al subir varios PDF seguidos | Reintento automático (hasta 2) respetando `Retry-After`; si persiste, mensaje claro "esperá un minuto". |
| Modelos de Groq que cambian de nombre / se dan de baja | Todos configurables por env (`GROQ_TEXT_MODEL`, etc.); error 404 con mensaje explicativo. |
| PDF escaneado (sin texto seleccionable) | Se detecta y se avisa: usar el PDF original del banco o cargar a mano. |
| Foto de ticket JPG/PNG (sin modelo con visión) | Mensaje que indica convertir a PDF; soporte listo vía `GROQ_VISION_MODEL`. |
| Resúmenes con formatos raros → extracción imperfecta | La pantalla de revisión permite destildar/ajustar antes de cargar. |
| SQLite y varios accesos simultáneos | Uso personal, 2 workers gunicorn. Suficiente. |
| La API key se compartió por chat | Recomendado rotarla en console.groq.com antes de publicar; en Fly va como secret. |
