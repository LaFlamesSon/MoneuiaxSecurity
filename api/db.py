import psycopg
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from config import settings

def _configure(conn: psycopg.Connection) -> None:
    register_vector(conn)

pool = ConnectionPool(conninfo=settings.database_url, min_size=1, max_size=10, configure=_configure)
