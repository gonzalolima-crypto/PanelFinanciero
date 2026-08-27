# Especificación — Panel Financiero

Documento de desarrollo guiado por especificaciones (SDD). Refleja lo acordado
en la reunión del 27/08/2026 (`tarea.md`) y las respuestas posteriores.

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
  y **subida de audio** transcripta en el servidor con Gemini.
- Interpretación de voz y de comprobantes movida al backend (la API key queda
  del lado del servidor, nunca en el navegador).

Fuera de alcance en v1 (se puede agregar después, es barato):

- Importación de CSV/Excel de banco en lote.
- Múltiples usuarios / cuentas separadas.
- Edición de un movimiento existente (hoy: borrar y volver a cargar).
- Adjuntar TXT como comprobante (hoy: imagen JPG/PNG y PDF).

## 3. Arquitectura

```
Navegador (HTML + JS + Chart.js)
        │  fetch /api/*
        ▼
Flask (app/)  ──►  SQLite3 (data/panel.db)
        │
        └──►  Google Gemini API (generativelanguage.googleapis.com)
                 · parse_voice   : texto hablado  → movimiento
                 · transcribe    : audio          → texto
                 · parse_attachment: imagen/PDF   → lista de consumos
```

- **Servidor de desarrollo**: `python run.py` (Flask, puerto 8000).
- **Servidor de producción**: `gunicorn wsgi:app` dentro de un contenedor
  Docker, desplegado en Fly.io con un volumen persistente montado en `/data`.

### 3.1 Modelo de datos (SQLite)

```sql
movements(
  id TEXT PK, type TEXT, date TEXT (YYYY-MM-DD),
  category TEXT, amount REAL, note TEXT, created_at TEXT
)
config(key TEXT PK, value TEXT)   -- hoy: goalPct
```

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
| POST | `/api/voice/parse` | `{text}` → movimiento sugerido (Gemini) |
| POST | `/api/voice/transcribe` | `audio` (multipart) → `{text}` (Gemini) |
| POST | `/api/attachment/parse` | `file` (multipart, imagen/PDF) → consumos (Gemini) |

Todas las rutas `/api/*` responden **401** si no hay sesión y la contraseña
está configurada.

### 3.3 Configuración (variables de entorno)

| Variable | Default | Uso |
|---|---|---|
| `APP_PASSWORD` | *(vacío)* | Contraseña de acceso. Vacío = sin protección (solo local). |
| `SECRET_KEY` | `dev-inseguro-cambiar` | Firma de cookies de sesión. |
| `GEMINI_API_KEY` | *(vacío)* | Clave de Google Gemini. Sin ella, voz y comprobantes fallan con 502. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Modelo a usar. |
| `DB_PATH` | `./data/panel.db` | Ruta del archivo SQLite. En Fly: `/data/panel.db`. |
| `UPLOAD_DIR` | `./data/uploads` | Carpeta de comprobantes subidos. |
| `MAX_CONTENT_MB` | `25` | Límite de tamaño de subida. |
| `PORT` | `8000` (local) / `8080` (Docker) | Puerto. |

## 4. Decisiones y justificación

| Decisión | Motivo |
|---|---|
| Flask + SQLite3 | Acordado en la reunión. Baja complejidad, una sola persona lo usa. |
| Gemini (nivel gratuito) | Sin costo para uso personal; soporta texto, imagen, PDF y audio en una sola API. Proveedor intercambiable por env. |
| API key en el backend | El prototipo la exponía en el navegador. Riesgo de robo de clave y de cuota. |
| Contraseña única (no login por usuario) | Uso personal. Suficiente para proteger un link público. |
| Fly.io | Nivel gratuito con **disco persistente** (SQLite sobrevive a los deploys) y salida a internet permitida (necesaria para llamar a Gemini). Render gratuito borra el disco; PythonAnywhere gratuito bloquea las llamadas salientes. |
| Chart.js servido localmente (`app/static/vendor/`) | La app funciona sin depender de un CDN. |
| Voz: dictado en vivo + audio al servidor | El dictado en vivo (Web Speech API) es gratis pero solo Chrome de escritorio/Android. La subida de audio cubre iPhone/Safari. |

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
  No consumen cuota de Gemini.
- Manuales (a cargo del usuario en local):
  - [ ] Dictar 3-4 movimientos por voz y verificar el formulario autocompletado.
  - [ ] Subir `Comprobantes/Resumen Visa Pago Agosto.pdf` y revisar la
        agrupación por categoría.
  - [ ] Subir `Comprobantes/Resumen Mastercard Pago Agosto.pdf`.
  - [ ] Sacar una foto de un ticket y adjuntarla.
  - [ ] Cerrar y reabrir la app; confirmar que los datos siguen ahí.
  - [ ] Probar desde el celular (misma red, `http://IP-de-la-PC:8000`).

## 7. Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| Cuota gratuita de Gemini agotada (timeout / 429) | Mensaje claro al usuario; reintentar más tarde. Modelo `flash` (más barato). |
| Formato de audio del navegador no soportado por Gemini | El dictado en vivo es la vía principal en Chrome; la subida acepta `.mp3/.wav/.ogg/.m4a`. A revisar en pruebas. |
| Resúmenes de tarjeta con formatos raros → extracción imperfecta | La pantalla de revisión permite destildar/ajustar antes de cargar. |
| SQLite y varios accesos simultáneos | Uso personal, 2 workers gunicorn. Suficiente. |
