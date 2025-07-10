"""Simple SQLite-based key-value store for application state."""

import sqlite3
from typing import Iterable, Optional


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

    def __enter__(self) -> "SqliteKV":
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Close the connection when leaving the context."""
        self.close()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self.conn.close()

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
        cur = self.conn.cursor()
        try:
            cur.execute(
                "REPLACE INTO state(key, value) VALUES(?, ?)",
                (key, value),
            )
            self.conn.commit()
        except sqlite3.DatabaseError:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def set_many(self, items: Iterable[tuple[str, str]]):
        """Insert multiple ``(key, value)`` pairs in a single transaction."""
        cur = self.conn.cursor()
        try:
            cur.executemany(
                "REPLACE INTO state(key, value) VALUES(?, ?)",
                items,
            )
            self.conn.commit()
        except sqlite3.DatabaseError:
            self.conn.rollback()
            raise
        finally:
            cur.close()
