import os

from dotenv import load_dotenv
from flask import Flask

from .db import init_db
from .routes import bp


def create_app(config=None):
    load_dotenv()

    app = Flask(__name__)
    app.config.update(
        DATABASE_URL=os.environ["DATABASE_URL"],
        CAPAS_DIR=os.environ.get(
            "CAPAS_DIR",
            os.path.join(app.root_path, "..", "dados", "capas"),
        ),
        ITENS_POR_PAGINA=24,
    )
    if config:
        app.config.update(config)

    init_db(app)
    app.register_blueprint(bp)
    return app
