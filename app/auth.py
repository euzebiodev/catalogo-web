"""Login único para a edição e proteção contra pedidos forjados (CSRF)."""

import functools
import hmac
import secrets

from flask import abort, current_app, redirect, request, session, url_for
from psycopg import errors as pg_errors
from werkzeug.security import check_password_hash, generate_password_hash


def edicao_disponivel(app):
    """A edição só existe se o login e o banco de escrita estiverem configurados."""
    return bool(app.config.get("EDICAO_ATIVA"))


def hash_atual(app):
    """Hash da senha em uso: o que foi trocado pelo site, ou o do ambiente se nunca foi trocado."""
    try:
        with app.extensions["db_pool_escrita"].connection() as conexao:
            linha = conexao.execute(
                "SELECT senha_hash FROM admin_senha WHERE usuario = %s",
                (app.config["ADMIN_USUARIO"],),
            ).fetchone()
    except pg_errors.UndefinedTable:
        # Migração 004 ainda não aplicada: continua valendo a senha do ambiente.
        linha = None
    if linha:
        return linha["senha_hash"]
    return app.config["ADMIN_SENHA_HASH"]


def senha_correta(app, senha):
    return check_password_hash(hash_atual(app), senha)


def trocar_senha(app, nova):
    """Grava a nova senha no banco. Levanta UndefinedTable se a migração 004 faltar."""
    with app.extensions["db_pool_escrita"].connection() as conexao:
        conexao.execute(
            """INSERT INTO admin_senha (usuario, senha_hash, atualizada_em)
               VALUES (%s, %s, now())
               ON CONFLICT (usuario)
               DO UPDATE SET senha_hash = EXCLUDED.senha_hash, atualizada_em = now()""",
            (app.config["ADMIN_USUARIO"], generate_password_hash(nova)),
        )


def logado():
    return bool(session.get("logado"))


def token_csrf():
    """Token da sessão, usado em todos os formulários que alteram algo."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def conferir_csrf():
    enviado = request.form.get("csrf", "")
    esperado = session.get("csrf", "")
    if not esperado or not hmac.compare_digest(enviado.encode(), esperado.encode()):
        abort(400)


def conferir_senha(app, usuario, senha):
    if not edicao_disponivel(app):
        return False
    usuario_ok = hmac.compare_digest(usuario.encode(), app.config["ADMIN_USUARIO"].encode())
    return usuario_ok and senha_correta(app, senha)


def proxima_segura(destino):
    """Só aceita caminhos internos do site, para o login não virar redirecionamento para fora."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("catalogo.inicio")


def exige_login(view):
    @functools.wraps(view)
    def protegida(*args, **kwargs):
        if not edicao_disponivel(current_app):
            abort(404)
        if not logado():
            return redirect(url_for("catalogo.entrar", proxima=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return protegida
