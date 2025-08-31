from __future__ import annotations
from pathlib import Path
from platformdirs import user_data_dir
import sqlite3
from typing import Iterable, Tuple
from datetime import datetime

APP_NAME = "CompressorAndPDFMerger"
APP_AUTHOR = "YourOrgOrName"

_conn: sqlite3.Connection | None = None

def _db_path() -> Path:
    data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.sqlite3"

def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_path())
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA synchronous=NORMAL;")
        _init_schema(_conn)
    return _conn

def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        ts       TEXT    NOT NULL,
        tab      TEXT    NOT NULL,
        action   TEXT    NOT NULL,
        src_name TEXT    NOT NULL,
        out_path TEXT    NOT NULL
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_history_ts ON history(ts DESC);")
    conn.commit()

def init_db() -> None:
    _ = _get_conn()

def add_history(tab: str, action: str, src_name: str, out_path: str, ts: str | None = None) -> None:
    if ts is None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    conn.execute(
        "INSERT INTO history(ts, tab, action, src_name, out_path) VALUES (?, ?, ?, ?, ?)",
        (ts, tab, action, src_name, out_path),
    )
    conn.commit()

def list_history(limit: int = 500) -> Iterable[Tuple[int, str, str, str, str, str]]:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT id, ts, tab, action, src_name, out_path FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return cur.fetchall()

def clear_history() -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM history;")
    conn.commit()
