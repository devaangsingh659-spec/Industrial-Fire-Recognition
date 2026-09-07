# backend/database/connection.py

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.pool import ThreadedConnectionPool


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "industrial_fire_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


# ============================================================
# DATABASE CONNECTION POOL (LAZY INITIALIZATION)
# ============================================================

_connection_pool = None


def get_pool():
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    return _connection_pool


# ============================================================
# GET CONNECTION
# ============================================================

def get_connection():
    """
    Get a PostgreSQL connection from the connection pool.
    """
    pool = get_pool()
    return pool.getconn()


# ============================================================
# RETURN CONNECTION
# ============================================================

def release_connection(connection):
    """
    Return the connection back to the connection pool.
    """
    if _connection_pool is not None and connection is not None:
        _connection_pool.putconn(connection)


# ============================================================
# CLOSE ALL CONNECTIONS
# ============================================================

def close_pool():
    """
    Close all PostgreSQL connections when the application stops.
    """
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
