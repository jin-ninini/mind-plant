from __future__ import annotations

from typing import Any


def get_growth_stage(completed_count: int) -> dict[str, Any]:
    count = max(0, int(completed_count))

    if count == 0:
        return {
            "stage": "씨앗",
            "level": 1,
            "emoji": "🌱",
            "message": "아직 작은 가능성이 잠들어 있어요",
            "next_target": 1,
        }
    if 1 <= count <= 2:
        return {
            "stage": "새싹",
            "level": 2,
            "emoji": "🌿",
            "message": "첫 실천으로 싹이 텄어요",
            "next_target": 3,
        }
    if 3 <= count <= 4:
        return {
            "stage": "어린잎",
            "level": 3,
            "emoji": "🪴",
            "message": "꾸준함이 보이기 시작했어요",
            "next_target": 5,
        }
    if 5 <= count <= 7:
        return {
            "stage": "줄기",
            "level": 4,
            "emoji": "🌳",
            "message": "스스로를 믿는 힘이 자라고 있어요",
            "next_target": 8,
        }

    return {
        "stage": "꽃",
        "level": 5,
        "emoji": "🌻",
        "message": "작은 목표들이 멋진 변화가 되었어요",
        "next_target": None,
    }


def build_plant_state(recommendation: dict[str, Any], completed_count: int) -> dict[str, Any]:
    growth = get_growth_stage(completed_count)

    return {
        "plant_name": str(recommendation.get("plant_name", "식물 친구")),
        "plant_id": str(recommendation.get("plant_id", "unknown")),
        "plant_emoji": str(recommendation.get("plant_emoji", "🌱")),
        "plant_symbol": str(recommendation.get("plant_symbol", "성장")),
        "plant_reason": str(recommendation.get("plant_reason", "작은 실천과 잘 맞는 식물이에요.")),
        "starter_goals": list(recommendation.get("starter_goals", []))[:3],
        "completed_count": max(0, int(completed_count)),
        "growth_stage": growth,
    }
