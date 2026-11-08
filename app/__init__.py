import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from .auth import logado, token_csrf
from .db import init_db
from .routes import bp


def create_app(config=None):
    load_dotenv()

    app = Flask(__name__)
    app.config.update(
        DATABASE_URL=os.environ["DATABASE_URL"],
        # Usuário com permissão de escrita, só para a edição. Sem ele, a edição fica desligada.
        DATABASE_URL_ESCRITA=os.environ.get("DATABASE_URL_ESCRITA"),
        ADMIN_USUARIO=os.environ.get("CATALOGO_ADMIN_USUARIO"),
        ADMIN_SENHA_HASH=os.environ.get("CATALOGO_ADMIN_SENHA_HASH"),
        SECRET_KEY=os.environ.get("CATALOGO_SECRET_KEY"),
        CAPAS_DIR=os.environ.get(
            "CAPAS_DIR",
            os.path.join(app.root_path, "..", "dados", "capas"),
        ),
        ITENS_POR_PAGINA=24,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    # A edição só liga com tudo configurado. O SECRET_KEY precisa ser fixo:
    # com dois workers do gunicorn, uma chave aleatória deixaria o login instável.
    if "EDICAO_ATIVA" not in app.config:
        app.config["EDICAO_ATIVA"] = all(
            app.config.get(chave)
            for chave in ("DATABASE_URL_ESCRITA", "ADMIN_USUARIO", "ADMIN_SENHA_HASH", "SECRET_KEY")
        )

    init_db(app)
    app.register_blueprint(bp)

    @app.context_processor
    def contexto_sessao():
        return {
            "logado": logado,
            "csrf_token": token_csrf,
            "edicao_ativa": app.config["EDICAO_ATIVA"],
        }

    return app
