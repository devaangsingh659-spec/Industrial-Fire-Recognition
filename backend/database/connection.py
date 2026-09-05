
import os

from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# ============================================================
# DATABASE CONNECTION POOL
# ============================================================

connection_pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,

    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)


# ============================================================
# GET CONNECTION
# ============================================================

def get_connection():
    """
    Get a PostgreSQL connection from the connection pool.
    """

    return connection_pool.getconn()


# ============================================================
# RETURN CONNECTION
# ============================================================

def release_connection(connection):
    """
    Return the connection back to the connection pool.
    """

    connection_pool.putconn(connection)


# ============================================================
# CLOSE ALL CONNECTIONS
# ============================================================

def close_pool():
    """
    Close all PostgreSQL connections when the application stops.
    """

    connection_pool.closeall()

