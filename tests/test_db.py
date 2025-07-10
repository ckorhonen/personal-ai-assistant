import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import SqliteKV


def test_set_get(tmp_path):
    db_file = tmp_path / "assistant.db"
    kv = SqliteKV(str(db_file))

    # Ensure seed value is created
    assert kv.get("last_history_id") == "0"

    kv.set("foo", "bar")
    assert kv.get("foo") == "bar"
    assert kv.get("missing", "default") == "default"
