"""Arranca la aplicación en tu computadora (modo desarrollo).

Uso:
    python run.py

Después abrí en el navegador:  http://localhost:8000
"""
from app import create_app
from app import config

app = create_app()

if __name__ == "__main__":
    print("\n  Panel Financiero corriendo en:  http://localhost:%d\n" % config.PORT)
    app.run(host="127.0.0.1", port=config.PORT, debug=True)
