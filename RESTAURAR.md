# Cómo retomar el proyecto (desde un backup)

Si estás abriendo esto desde un ZIP de backup:

1. **Descomprimí el ZIP** en una carpeta (por ejemplo, de vuelta en el Escritorio,
   quedando `Proyecto Panel Financiero`).
2. Doble clic en **`iniciar.bat`**.
   - La carpeta `.venv` (el "motor" de Python) **no viene en el backup** porque es
     pesada y se regenera sola. La primera vez que corras `iniciar.bat` la crea de
     nuevo (tarda unos minutos). Es normal.
3. Se abre el navegador en `http://127.0.0.1:8000`. Listo.

## Qué incluye el backup

- Todo el código (`app/`, `run.py`, `tests/`, etc.)
- `.env` con tu clave de Groq (¡no lo compartas!)
- La documentación (`GUIA.md`, `ESPECIFICACION.md`)
- La base de datos con tus movimientos (`data/panel.db`), si existía
- El historial de cambios (`.git/`) — también está en GitHub:
  https://github.com/gonzalolima-crypto/PanelFinanciero

## Qué NO incluye (y no hace falta)

- `.venv/` — se regenera con `iniciar.bat`
- Archivos temporales (`__pycache__`, `.pytest_cache`)

## Para seguir desarrollando

Ver **`GUIA.md`** (sección 3 "Cómo hacer ajustes comunes" y sección 4 para el
despliegue en Fly.io). El estado y las decisiones están en **`ESPECIFICACION.md`**.
