import sqlite3

from app.core.config import get_settings


def get_connection():
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
