"""Fábrica de la aplicación Flask."""
from datetime import timedelta
import logging

from flask import Flask, jsonify

from . import config as app_config
from . import auth, db, routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=app_config.SECRET_KEY,
        MAX_CONTENT_LENGTH=app_config.MAX_CONTENT_LENGTH,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.json.ensure_ascii = False

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
