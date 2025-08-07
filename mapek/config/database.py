import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from mapek.config.settings import config

class DatabasePool:
    def __init__(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5, maxconn=20,
            host=config.db_host, database=config.db_name,
            user=config.db_user, password=config.db_pass
        )

    @contextmanager
    def get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

db_pool = DatabasePool()

@contextmanager
def database_transaction():
    with db_pool.get_connection() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
