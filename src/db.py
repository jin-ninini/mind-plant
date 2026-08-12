from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = "data/mindplant.db"


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(__file__).resolve().parent.parent / p


def _connect(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    return conn


def normalize_name(name: str) -> str:
    # 앞뒤 공백 제거 + 중복 공백 정리로 같은 사용자를 동일 키로 취급합니다.
    return " ".join(str(name or "").split()).strip()


def user_exists(name: str, path: str = DEFAULT_DB_PATH) -> bool:
    normalized = normalize_name(name)
    if not normalized:
        return False
    with _connect(path) as conn:
        row = conn.execute("SELECT 1 FROM users WHERE name = ?", (normalized,)).fetchone()
    return row is not None


def load_user_state(name: str, path: str = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    normalized = normalize_name(name)
    if not normalized:
        return None
    with _connect(path) as conn:
        row = conn.execute("SELECT state_json FROM users WHERE name = ?", (normalized,)).fetchone()
    if not row:
        return None
    try:
        state = json.loads(row[0])
    except (TypeError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def save_user_state(name: str, state: dict[str, Any], path: str = DEFAULT_DB_PATH) -> None:
    normalized = normalize_name(name)
    if not normalized:
        return
    payload = json.dumps(state, ensure_ascii=False)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO users (name, state_json, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
            """,
            (normalized, payload),
        )
        conn.commit()
