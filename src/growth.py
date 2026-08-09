from __future__ import annotations

from typing import Any


EXP_PER_COMPLETION = 500


GROWTH_RULES: tuple[dict[str, Any], ...] = (
    {
        "min": 0,
        "max": 0,
        "stage": "씨앗",
        "level": 1,
        "emoji": "🌱",
        "message": "아직 작은 가능성이 잠들어 있어요",
        "next_target": 1,
    },
    {
        "min": 1,
        "max": 2,
        "stage": "새싹",
        "level": 2,
        "emoji": "🌿",
        "message": "첫 실천으로 싹이 텄어요",
        "next_target": 3,
    },
    {
        "min": 3,
        "max": 5,
        "stage": "어린잎",
        "level": 3,
        "emoji": "🪴",
        "message": "꾸준함이 보이기 시작했어요",
        "next_target": 6,
    },
    {
        "min": 6,
        "max": 9,
        "stage": "줄기",
        "level": 4,
        "emoji": "🌳",
        "message": "스스로를 믿는 힘이 자라고 있어요",
        "next_target": 10,
    },
    {
        "min": 10,
        "max": None,
        "stage": "꽃",
        "level": 5,
        "emoji": "🌻",
        "message": "작은 목표들이 멋진 변화가 되었어요",
        "next_target": None,
    },
)


def get_growth_stage(completed_count: int) -> dict[str, Any]:
    count = max(0, int(completed_count))

    for rule in GROWTH_RULES:
        lower = int(rule["min"])
        upper = rule["max"]
        if count < lower:
            continue
        if upper is not None and count > int(upper):
            continue
        return {
            "stage": str(rule["stage"]),
            "level": int(rule["level"]),
            "emoji": str(rule["emoji"]),
            "message": str(rule["message"]),
            "next_target": rule["next_target"],
        }

    # 규칙이 비어 있거나 비정상일 때를 위한 안전 fallback
    return {
        "stage": "씨앗",
        "level": 1,
        "emoji": "🌱",
        "message": "아직 작은 가능성이 잠들어 있어요",
        "next_target": 1,
    }


def get_next_stage_preview(completed_count: int) -> dict[str, Any] | None:
    count = max(0, int(completed_count))
    current = get_growth_stage(count)
    next_target = current.get("next_target")
    if next_target is None:
        return None

    next_rule = next(
        (rule for rule in GROWTH_RULES if int(rule.get("min", 0) or 0) == int(next_target)),
        None,
    )
    if next_rule is None:
        return None

    return {
        "stage": str(next_rule["stage"]),
        "emoji": str(next_rule["emoji"]),
        "message": str(next_rule["message"]),
        "remaining": max(0, int(next_target) - count),
    }


def get_growth_progress(completed_count: int) -> dict[str, Any]:
    count = max(0, int(completed_count))
    stage = get_growth_stage(count)
    level = int(stage.get("level", 1) or 1)
    total_exp = count * EXP_PER_COMPLETION

    current_rule = next((rule for rule in GROWTH_RULES if int(rule.get("level", 0) or 0) == level), GROWTH_RULES[0])
    start_count = int(current_rule.get("min", 0) or 0)
    level_start_exp = start_count * EXP_PER_COMPLETION
    next_target = stage.get("next_target")

    if next_target is None:
        return {
            "total_exp": total_exp,
            "current_level_exp": total_exp - level_start_exp,
            "required_level_exp": None,
            "next_level_total_exp": None,
            "is_max_level": True,
        }

    next_level_total_exp = int(next_target) * EXP_PER_COMPLETION
    required_level_exp = max(1, next_level_total_exp - level_start_exp)
    current_level_exp = min(required_level_exp, max(0, total_exp - level_start_exp))

    return {
        "total_exp": total_exp,
        "current_level_exp": current_level_exp,
        "required_level_exp": required_level_exp,
        "next_level_total_exp": next_level_total_exp,
        "is_max_level": False,
    }


def build_plant_state(recommendation: dict[str, Any], completed_count: int) -> dict[str, Any]:
    growth = get_growth_stage(completed_count)
    growth_progress = get_growth_progress(completed_count)

    return {
        "plant_name": str(recommendation.get("plant_name", "식물 친구")),
        "plant_id": str(recommendation.get("plant_id", "unknown")),
        "plant_emoji": str(recommendation.get("plant_emoji", "🌱")),
        "plant_symbol": str(recommendation.get("plant_symbol", "성장")),
        "plant_reason": str(recommendation.get("plant_reason", "작은 실천과 잘 맞는 식물이에요.")),
        "starter_goals": list(recommendation.get("starter_goals", []))[:3],
        "completed_count": max(0, int(completed_count)),
        "growth_stage": growth,
        "growth_progress": growth_progress,
    }
