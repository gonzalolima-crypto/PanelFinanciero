"""Arranca la aplicación en tu computadora (modo desarrollo).

Uso:
    python run.py

Después abrí en el navegador:  http://127.0.0.1:8000

Variables opcionales:
    HOST=127.0.0.1   -> solo esta computadora (por defecto 0.0.0.0: también el celular en la misma WiFi)
    FLASK_DEBUG=1    -> recarga automática al cambiar el código
"""
import os

from app import create_app
from app import config

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0"
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in ("1", "true", "yes", "si", "sí")

    print()
    print("  ============================================================")
    print("   PANEL FINANCIERO EN MARCHA")
    print("  ============================================================")
    print(f"   En esta computadora:            http://127.0.0.1:{config.PORT}")
    if host == "0.0.0.0":
        print(f"   Desde el celular (misma WiFi):  http://<IP-de-esta-PC>:{config.PORT}")
    print("  ============================================================")
    print("   Para apagar: cerrá esta ventana o presioná Ctrl+C.")
    print("  ============================================================")
    print()

    app.run(host=host, port=config.PORT, debug=debug, use_reloader=debug)
