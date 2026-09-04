"""Fábrica de la aplicación Flask."""
from datetime import timedelta
import logging
import mimetypes

from flask import Flask, jsonify

from . import config as app_config
from . import auth, db, routes

# Los tipos de archivo se registran ACÁ, al importar el módulo (un solo hilo).
# El módulo `mimetypes` de Python se inicializa solo la primera vez que se lo
# usa, y esa inicialización no es segura con varios hilos: si dos pedidos de
# archivos estáticos entran a la vez recién arrancado el servidor, uno puede
# recibir "text/plain" y el navegador rechaza el CSS (y lo cachea mal).
mimetypes.init()
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")

# Se agrega como ?v=... a las URLs de los estáticos. Subir este número obliga a
# los navegadores a volver a bajar CSS/JS aunque los tengan cacheados.
STATIC_VERSION = "2"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=app_config.SECRET_KEY,
        MAX_CONTENT_LENGTH=app_config.MAX_CONTENT_LENGTH,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # 1 hora: si alguna vez se cachea algo mal, se corrige solo enseguida.
        SEND_FILE_MAX_AGE_DEFAULT=timedelta(hours=1),
    )
    app.json.ensure_ascii = False

    # Disponible en las plantillas como {{ v }} para el ?v= de los estáticos.
    app.jinja_env.globals["v"] = STATIC_VERSION

    logging.basicConfig(level=logging.INFO)

    db.init_db()
    app.teardown_appcontext(db.close_db)

    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)

    if not app_config.APP_PASSWORD:
        app.logger.warning(
            "APP_PASSWORD no está configurada: el panel queda SIN protección. "
            "Configurala antes de publicar la app."
        )
    if not app_config.GROQ_API_KEY:
        app.logger.warning(
            "GROQ_API_KEY no está configurada: la carga por voz y por comprobante "
            "no van a funcionar hasta que la agregues al .env."
        )

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": f"El archivo supera el límite de {app_config.MAX_CONTENT_MB} MB."}), 413

    return app
