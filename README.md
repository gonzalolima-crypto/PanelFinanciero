# Panel Financiero

Aplicación web personal de control de finanzas: gastos diarios, gastos con
tarjeta, impuestos, ingresos y ahorro. Carga manual, **por voz** (dictado o
audio) o **adjuntando comprobantes en PDF** (resumen de tarjeta / ticket),
interpretados con modelos de Groq.

- **Backend:** Flask + SQLite3
- **Frontend:** HTML + JavaScript + Chart.js (servido localmente)
- **IA:** Groq — `openai/gpt-oss-120b` (texto), `whisper-large-v3-turbo` (audio).
  PDF de comprobantes: texto extraído con PyMuPDF y estructurado por el modelo.
- **Despliegue:** Docker + Fly.io

## Arranque rápido (Windows)

Doble clic en **`iniciar.bat`**. La primera vez instala todo. La clave de Groq
(`GROQ_API_KEY`) ya viene cargada en `.env`; si querés proteger el panel,
completá `APP_PASSWORD` en ese archivo y volvé a iniciarlo.

## Arranque manual

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux/Mac
cp .env.example .env        # y completar valores
python run.py               # http://127.0.0.1:8000
```

## Pruebas

```bash
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

## Documentación

- **`GUIA.md`** — paso a paso no técnico: generar la clave de Gemini, levantar
  la app, ajustes comunes y publicación en Fly.io.
- **`ESPECIFICACION.md`** — alcance, arquitectura, API, decisiones y plan.
