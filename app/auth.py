"""Autenticación por contraseña única.

- Si APP_PASSWORD está vacía, el panel queda abierto (solo para pruebas locales).
- Si está configurada, se pide una vez y queda guardada en la sesión (cookie firmada).
"""
import hmac
from functools import wraps

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from . import config

bp = Blueprint("auth", __name__)


def password_required() -> bool:
    return bool(config.APP_PASSWORD)


def is_authenticated() -> bool:
    return (not password_required()) or session.get("auth") is True


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
