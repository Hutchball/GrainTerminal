"""
db_config.py
============
Connection abstraction layer.  All scripts import get_connection() from here
rather than calling sqlite3.connect() directly.

To use SQLite (default):
    python3 script.py

To use PostgreSQL when ready:
    DB_TYPE=postgres DATABASE_URL=postgresql://user:pass@host/db python3 script.py

The PostgreSQL path requires psycopg2:  pip install psycopg2-binary
"""

import os

DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()


def get_connection():
    """Return a database connection.  Caller is responsible for .close()."""
    if DB_TYPE == "postgres":
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError(
                "psycopg2 not installed. Run: pip install psycopg2-binary"
            )
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DB_TYPE=postgres requires DATABASE_URL env var")
        return psycopg2.connect(url)

    # Default: SQLite
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).parent / "grain_terminal.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def placeholder(n: int = 1) -> str:
    """Return the correct parameterised placeholder for the active DB type.
    SQLite uses ?, PostgreSQL uses %s.
    """
    mark = "%s" if DB_TYPE == "postgres" else "?"
    if n == 1:
        return mark
    return ", ".join([mark] * n)
