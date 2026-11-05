from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def init_db(app):
    pool = ConnectionPool(
        app.config["DATABASE_URL"],
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    app.extensions["db_pool"] = pool


def fetch_all(app, sql, params=()):
    with app.extensions["db_pool"].connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(app, sql, params=()):
    with app.extensions["db_pool"].connection() as conn:
        return conn.execute(sql, params).fetchone()
