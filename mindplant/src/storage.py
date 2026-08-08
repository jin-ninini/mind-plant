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
    """
    상대 경로를 실제 파일 위치로 바꿔줍니다.
    1순위: 현재 작업 디렉터리(cwd) 기준 (프로젝트 루트에서 실행하는 일반적인 경우)
    2순위: 프로젝트 루트 기준 (src/의 부모 폴더) - cwd가 다르게 설정된 경우 대비
    """
    p = Path(path)
    if p.is_absolute():
        return p

    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path

    project_root = Path(__file__).resolve().parent.parent
    return project_root / p


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
