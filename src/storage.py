from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_USER_DATA: dict[str, Any] = {
    "page": "start",
    "concern_type": "",
    "survey_answers": {
        "cautious": 3,
        "needs_support": 3,
        "focus": 3,
        "interest_oriented": 3,
        "small_steps": 3,
    },
    "free_text": "",
    "recommendation": None,
    "completed_count": 0,
    "today_goal": "",
    "last_encouragement": "",
}


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(__file__).resolve().parent.parent / p


def _deepcopy_default() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_USER_DATA, ensure_ascii=False))


def load_user_data(path: str = "data/demo_user.json") -> dict[str, Any]:
    target = _resolve_path(path)
    if not target.exists():
        return _deepcopy_default()

    try:
        with target.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            return _deepcopy_default()
    except Exception:
        return _deepcopy_default()

    merged = _deepcopy_default()
    merged.update(loaded)

    if not isinstance(merged.get("survey_answers"), dict):
        merged["survey_answers"] = _deepcopy_default()["survey_answers"]

    return merged


def save_user_data(data: dict[str, Any], path: str = "data/demo_user.json") -> None:
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reset_user_data(path: str = "data/demo_user.json") -> None:
    save_user_data(_deepcopy_default(), path)
