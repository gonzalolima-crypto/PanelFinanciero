# Panel Financiero

Aplicación web personal de control de finanzas: gastos diarios, gastos con
tarjeta, impuestos, ingresos y ahorro. Carga manual, **por voz** o **adjuntando
comprobantes** (foto de ticket / PDF de resumen de tarjeta), interpretados con
Google Gemini.

- **Backend:** Flask + SQLite3
- **Frontend:** HTML + JavaScript + Chart.js (servido localmente)
- **IA:** Google Gemini (nivel gratuito)
- **Despliegue:** Docker + Fly.io

## Arranque rápido (Windows)

Doble clic en **`iniciar.bat`**. La primera vez instala todo y crea `.env`;
completá `GEMINI_API_KEY` y `APP_PASSWORD` en ese archivo y volvé a iniciarlo.

## Arranque manual

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux/Mac
cp .env.example .env        # y completar valores
python run.py               # http://localhost:8000
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
