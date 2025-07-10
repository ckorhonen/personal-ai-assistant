"""Simple SQLite-based key-value store for application state."""

import sqlite3
from typing import Optional


class SqliteKV:
    """Key-value storage backed by an SQLite database."""

    def __init__(self, db_path: str = "assistant.db") -> None:
        """Create or connect to the SQLite database and ensure schema.

        Parameters
        ----------
        db_path: str, optional
            Path to the SQLite database file. Defaults to ``"assistant.db"``.
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS state(
              key TEXT PRIMARY KEY,
              value TEXT
            );
            """
        )
        self.conn.commit()
        self._ensure_seed()

    def _ensure_seed(self) -> None:
        """Insert the default ``last_history_id`` row if missing."""
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM state WHERE key=?", ("last_history_id",))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO state(key, value) VALUES(?, ?)",
                ("last_history_id", "0"),
            )
            self.conn.commit()
        cur.close()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve the value for ``key`` from the store."""
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM state WHERE key=?", (key,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return default
        return row[0]

    def set(self, key: str, value: str) -> None:
        """Store ``value`` for ``key`` in the database."""
        self.conn.execute(
            "REPLACE INTO state(key, value) VALUES(?, ?)",
            (key, value),
        )
        self.conn.commit()
