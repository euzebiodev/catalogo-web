from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def _pool(url, tamanho):
    return ConnectionPool(
        url,
        min_size=1,
        max_size=tamanho,
        kwargs={"row_factory": dict_row},
        open=True,
    )


def init_db(app):
    app.extensions["db_pool"] = _pool(app.config["DATABASE_URL"], 5)
    # Pool de escrita só existe quando a edição está configurada.
    if app.config.get("DATABASE_URL_ESCRITA"):
        app.extensions["db_pool_escrita"] = _pool(app.config["DATABASE_URL_ESCRITA"], 2)


def fetch_all(app, sql, params=()):
    with app.extensions["db_pool"].connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(app, sql, params=()):
    with app.extensions["db_pool"].connection() as conn:
        return conn.execute(sql, params).fetchone()
