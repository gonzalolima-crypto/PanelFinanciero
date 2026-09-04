"""Autenticación por contraseña única.

- Si APP_PASSWORD está vacía, el panel queda abierto (solo para pruebas locales).
- Si está configurada, se pide una vez y queda guardada en la sesión (cookie firmada).
- La sesión guarda además una huella de la contraseña: si se cambia
  APP_PASSWORD, todas las sesiones abiertas dejan de valer y hay que volver a
  entrar. (Si no, cambiar la clave no echaría a quien ya estaba adentro.)
"""
import hashlib
import hmac
from functools import wraps

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from . import config

bp = Blueprint("auth", __name__)


def password_required() -> bool:
    return bool(config.APP_PASSWORD)


def _password_fingerprint() -> str:
    """Huella corta de la contraseña actual (no permite reconstruirla)."""
    return hashlib.sha256(config.APP_PASSWORD.encode("utf-8")).hexdigest()[:16]


def is_authenticated() -> bool:
    if not password_required():
        return True
    if session.get("auth") is not True:
        return False
    # Si la contraseña cambió, la huella guardada ya no coincide -> a loguearse.
    return hmac.compare_digest(str(session.get("pw", "")), _password_fingerprint())


def check_password(candidate: str) -> bool:
    if not password_required():
        return True
    return hmac.compare_digest(str(candidate or ""), config.APP_PASSWORD)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if is_authenticated():
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "No autenticado. Iniciá sesión de nuevo."}), 401
        return redirect(url_for("auth.login", next=request.path))

    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("main.index"))

    error = None
    if request.method == "POST":
        if check_password(request.form.get("password", "")):
            session["auth"] = True
            session["pw"] = _password_fingerprint()
            session.permanent = True
            dest = request.args.get("next") or url_for("main.index")
            if not dest.startswith("/"):
                dest = url_for("main.index")
            return redirect(dest)
        error = "Contraseña incorrecta."

    return render_template("login.html", error=error)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
