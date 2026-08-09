from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"

DEFAULT_PLANTS: list[dict[str, Any]] = [
    {
        "id": "sunflower",
        "name": "해바라기",
        "emoji": "🌻",
        "keywords": ["진로", "방향", "희망", "활력"],
        "concern_types": ["career"],
        "personality_fit": "밝은 에너지로 다양한 것에 도전하며 방향을 찾고 싶은 사용자",
        "symbol": "방향성, 희망, 활력",
        "description": "빛을 향해 고개를 돌리는 해바라기처럼, 너의 진로 방향을 긍정적으로 찾도록 응원하는 식물 친구예요.",
        "starter_goals": [
            "관심 있는 직업 1개 찾아보기",
            "좋아하는 과목이나 활동 3개 적어보기",
            "진로 관련 짧은 영상 10분 보기",
        ],
    },
    {
        "id": "stuckii",
        "name": "스투키",
        "emoji": "🌵",
        "keywords": ["집중", "독립", "단단함", "방해 차단"],
        "concern_types": ["focus", "habit"],
        "personality_fit": "복잡한 관리 없이 스스로 짧고 강하게 집중하는 사용자",
        "symbol": "인내, 독립, 단단함",
        "description": "손이 많이 가지 않아도 단단하게 자라는 스투키처럼, 짧은 몰입을 반복해 집중 근육을 키우게 도와줘요.",
        "starter_goals": [
            "25분 타이머로 한 과제만 하기",
            "집중 시간에 휴대폰 뒤집어 두기",
            "끝난 뒤 5분 쉬고 다시 1회 반복하기",
        ],
    },
    {
        "id": "rosemary",
        "name": "로즈마리",
        "emoji": "🌱",
        "keywords": ["루틴", "원칙", "실용", "꾸준함"],
        "concern_types": ["habit"],
        "personality_fit": "정해진 원칙과 루틴으로 꾸준히 실천하고 싶은 사용자",
        "symbol": "성실함, 실용성, 꾸준함",
        "description": "향긋한 향을 꾸준히 내어주는 로즈마리처럼, 작은 반복을 쌓아 나만의 루틴을 만들어줘요.",
        "starter_goals": [
            "같은 시간에 공부 15분 시작하기",
            "할 일 체크박스 3개 만들기",
            "잠들기 전 내일 목표 1개 정하기",
        ],
    },
]

REQUIRED_RESULT_KEYS = [
    "personality_summary",
    "concern_summary",
    "plant_name",
    "plant_id",
    "plant_emoji",
    "plant_reason",
    "plant_symbol",
    "starter_goals",
    "message",
]


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p

    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path

    return Path(__file__).resolve().parent / p


def _safe_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _env_text(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip().strip('"').strip("'")


def _get_api_key() -> str:
    return _env_text("APIM_KEY") or _env_text("OPENAI_API_KEY") or _env_text("GEMINI_API_KEY")


def _get_model() -> str:
    return _env_text("CHAT_MODEL") or _env_text("OPENAI_MODEL", "gemini-3.1-flash-lite")


def _get_base_url(model: str) -> str:
    apim_base = _env_text("APIM_BASE_URL")
    if apim_base:
        # Foundry Proxy 구조: {APIM_BASE_URL}/{MODEL_NAME}/
        return f"{apim_base.rstrip('/')}/{model}/"

    base_url = _env_text("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    return base_url if base_url.endswith("/") else f"{base_url}/"


def _log_ai_error(context: str, exc: Exception) -> None:
    print(f"[MindPlant AI] {context} failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def _chat_completion_text(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    from openai import OpenAI

    api_key = _get_api_key()
    model = _get_model()
    is_apim = bool(_env_text("APIM_BASE_URL"))

    client = OpenAI(
        api_key=api_key,
        base_url=_get_base_url(model),
        default_headers={"api-key": api_key} if is_apim else None,
        timeout=20.0,
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )
    return _safe_text(response.choices[0].message.content)


def _get_concern_summary(concern_type: str) -> str:
    mapping = {
        "career": "진로 방향을 정하는 데 어려움을 느끼고 있어요.",
        "focus": "집중 흐름이 자주 끊겨서 시작이 부담스러워요.",
        "habit": "목표를 꾸준히 이어가는 습관 만들기가 고민이에요.",
    }
    return mapping.get(concern_type, "지금의 고민을 작은 실천으로 풀어가고 싶어요.")


def _get_personality_summary(survey_answers: dict[str, Any]) -> str:
    cautious = int(survey_answers.get("cautious", 3) or 3)
    needs_support = int(survey_answers.get("needs_support", 3) or 3)
    focus = int(survey_answers.get("focus", 3) or 3)
    interest_oriented = int(survey_answers.get("interest_oriented", 3) or 3)
    small_steps = int(survey_answers.get("small_steps", 3) or 3)

    traits: list[str] = []
    if cautious >= 4:
        traits.append("신중한 편")
    if needs_support >= 4:
        traits.append("응원이 있을 때 힘이 나는 편")
    if focus <= 2:
        traits.append("짧은 몰입부터 시작하면 잘하는 편")
    if interest_oriented >= 4:
        traits.append("흥미가 생기면 몰입이 빨라지는 편")
    if small_steps >= 4:
        traits.append("작은 단계로 시작할 때 꾸준한 편")

    if not traits:
        return "자신의 속도로 차근차근 실천을 이어갈 수 있는 성향"

    return ", ".join(traits) + "이에요."


def _concern_label(concern_type: str) -> str:
    mapping = {
        "career": "진로 고민",
        "focus": "집중 고민",
        "habit": "습관 고민",
    }
    return mapping.get(_safe_text(concern_type).lower(), "일반 고민")


# 고민 주제별로 AI 응답의 어조/역할을 바꾸는 페르소나 정의
PERSONAS: dict[str, dict[str, str]] = {
    "career": {
        "name": "진로 탐험 코치",
        "tone": "밝고 호기심 많은 어조로 다양한 가능성을 함께 탐색하며 방향을 찾도록 돕는다",
        "focus": "관심사와 강점을 발견하는 작은 진로 탐색 행동을 제안하는 데 집중한다",
    },
    "focus": {
        "name": "몰입 코치",
        "tone": "간결하고 에너지 있는 어조로 짧고 강한 실행을 응원한다",
        "focus": "집중이 흐트러지지 않도록 아주 짧은 몰입 행동과 환경 정리를 제안하는 데 집중한다",
    },
    "habit": {
        "name": "루틴 코치",
        "tone": "차분하고 안정적인 어조로 꾸준함과 반복을 응원한다",
        "focus": "작은 반복을 매일 이어가도록 습관 형성 행동을 제안하는 데 집중한다",
    },
    "custom": {
        "name": "고민 동반자",
        "tone": "유연하고 다정한 어조로 사용자가 말한 고유한 고민에 맞춰 대화한다",
        "focus": "사용자가 입력한 주제에 맞는 맞춤형 작은 행동을 제안하는 데 집중한다",
    },
}

# 설문 성향 점수가 임계값을 넘을 때 페르소나 어조에 덧붙이는 힌트
TRAIT_HINTS: dict[str, str] = {
    "cautious": "결정 전에 근거와 계획을 한 번 더 짚어주며 신중하게 안내한다",
    "needs_support": "자주 격려하고 곁에 있다는 확신을 주는 말을 더한다",
    "low_focus": "집중이 오래 가지 않아도 괜찮다고 안심시키며 아주 짧은 몰입 단위로 제안한다",
    "interest_oriented": "흥미로운 포인트를 짚어주며 재미 요소를 살린 제안을 더한다",
    "small_steps": "아주 작은 단계로 쪼개어 제안하는 것을 우선한다",
}


def _get_trait_hints(survey_answers: dict[str, Any]) -> list[str]:
    if not isinstance(survey_answers, dict):
        return []

    hints: list[str] = []
    if int(survey_answers.get("cautious", 3) or 3) >= 4:
        hints.append(TRAIT_HINTS["cautious"])
    if int(survey_answers.get("needs_support", 3) or 3) >= 4:
        hints.append(TRAIT_HINTS["needs_support"])
    if int(survey_answers.get("focus", 3) or 3) <= 2:
        hints.append(TRAIT_HINTS["low_focus"])
    if int(survey_answers.get("interest_oriented", 3) or 3) >= 4:
        hints.append(TRAIT_HINTS["interest_oriented"])
    if int(survey_answers.get("small_steps", 3) or 3) >= 4:
        hints.append(TRAIT_HINTS["small_steps"])
    return hints


def _get_persona(concern_type: str, survey_answers: dict[str, Any] | None = None) -> dict[str, str]:
    key = _safe_text(concern_type).lower()
    base = PERSONAS.get(key, PERSONAS["custom"])

    hints = _get_trait_hints(survey_answers or {})
    if not hints:
        return base

    persona = dict(base)
    persona["tone"] = base["tone"] + "; " + "; ".join(hints)
    return persona


def _survey_trait_summary(survey_answers: dict[str, Any]) -> str:
    if not isinstance(survey_answers, dict):
        return "균형형"

    cautious = int(survey_answers.get("cautious", 3) or 3)
    support = int(survey_answers.get("needs_support", 3) or 3)
    focus = int(survey_answers.get("focus", 3) or 3)
    interest_oriented = int(survey_answers.get("interest_oriented", 3) or 3)
    small = int(survey_answers.get("small_steps", 3) or 3)

    traits: list[str] = []
    if cautious >= 4:
        traits.append("신중형")
    if support >= 4:
        traits.append("응원형")
    if focus <= 2:
        traits.append("짧은집중형")
    if interest_oriented >= 4:
        traits.append("흥미주도형")
    if small >= 4:
        traits.append("작은단계형")

    return ", ".join(traits) if traits else "균형형"


def _split_goal_into_small_steps(goal: str) -> list[str]:
    target = goal.strip() or "오늘 목표"
    return [
        f"1) '{target}' 시작할 시간과 장소 딱 정하기",
        f"2) 그 시간에 '{target}'의 가장 쉬운 부분만 10분 해보기",
        "3) 끝나면 완료 버튼 누르고 어디까지 했는지 한 줄 남기기",
    ]


def _fallback_companion_reply(
    user_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    goal_history: list[str],
) -> str:
    message = _safe_text(user_text)
    lowered = message.lower()

    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    goals = [str(g).strip() for g in recommendation.get("starter_goals", []) if str(g).strip()]
    done_set = {g.strip() for g in goal_history if g and g.strip()}
    suggestion = next((g for g in goals if g not in done_set), goals[0] if goals else "오늘 10분만 집중해서 할 일 1개 정하기")

    if any(key in lowered for key in ["추천", "목표", "뭐할", "무엇", "해야"]):
        steps = "\n".join(_split_goal_into_small_steps(suggestion))
        return f"{plant_name} 기준으로 '{suggestion}'을(를) 작은 단계로 나눠볼게요.\n{steps}"

    if any(key in lowered for key in ["기억", "지난", "과거", "전에", "했었"]):
        if goal_history:
            recent = " / ".join(goal_history[-3:])
            return f"기억하고 있어요. 최근 완료한 목표는 {recent}예요. 다음엔 '{suggestion}' 어때요?"
        return f"아직 기록된 완료 목표가 없어요. 첫 목표로 '{suggestion}'부터 시작해볼까요?"

    if any(key in lowered for key in ["응원", "힘들", "지쳐", "불안", "걱정"]):
        return f"괜찮아요. {plant_name}도 작은 한 걸음을 좋아해요. 오늘은 10분만 투자해서 '{suggestion}'을(를) 해봐요."

    concern_label = _concern_label(concern_type)
    trait_text = _survey_trait_summary(survey_answers)
    stage_label = f"완료 {max(0, int(completed_count))}회"
    return (
        f"지금은 {concern_label} 흐름이고 성향은 {trait_text}에 가까워요. "
        f"현재는 {stage_label}이니 오늘 목표로 '{suggestion}'을(를) 추천할게요."
    )


def _score_plant(plant: dict[str, Any], user_profile: dict[str, Any]) -> float:
    concern_type = _safe_text(user_profile.get("concern_type")).lower()
    survey_answers = user_profile.get("survey_answers") or {}
    free_text = _safe_text(user_profile.get("free_text")).lower()

    score = 0.0

    concern_types = plant.get("concern_types") or []
    if concern_type and concern_type in concern_types:
        score += 5.0

    keywords = [str(k).lower() for k in (plant.get("keywords") or [])]
    if free_text:
        for keyword in keywords:
            if keyword and keyword in free_text:
                score += 2.0

    focus_score = int(survey_answers.get("focus", 3) or 3)
    small_steps = int(survey_answers.get("small_steps", 3) or 3)
    needs_support = int(survey_answers.get("needs_support", 3) or 3)

    plant_id = _safe_text(plant.get("id"))
    if plant_id in {"stuckii", "staghorn_fern"} and focus_score <= 2:
        score += 1.5
    if plant_id in {"rosemary", "stuckii"} and small_steps >= 4:
        score += 1.5
    if plant_id in {"lavender", "sunflower"} and needs_support >= 4:
        score += 1.0

    return score


def _clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _parse_json_relaxed(raw_text: str) -> Any:
    # 모델이 JSON 앞뒤로 설명문을 붙여도 가장 바깔쪽 괄호 구간만 추출해 파싱한다
    text = _clean_json_text(raw_text)
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass

    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    end_candidates = [i for i in (text.rfind("}"), text.rfind("]")) if i != -1]
    if start_candidates and end_candidates:
        start = min(start_candidates)
        end = max(end_candidates)
        if end > start:
            return json.loads(text[start : end + 1])

    raise ValueError(f"Unable to parse JSON from model output: {text[:200]}")


def _ensure_three_goals(goals: Any, fallback_goals: list[str]) -> list[str]:
    if isinstance(goals, list):
        clean = [str(g).strip() for g in goals if str(g).strip()]
    else:
        clean = []

    merged = clean[:3]
    for goal in fallback_goals:
        if len(merged) >= 3:
            break
        if goal not in merged:
            merged.append(goal)

    while len(merged) < 3:
        merged.append("오늘 할 수 있는 10분 행동 하나 정해보기")

    return merged


def _plant_by_id(plants: list[dict[str, Any]], plant_id: str) -> dict[str, Any] | None:
    for plant in plants:
        if _safe_text(plant.get("id")) == plant_id:
            return plant
    return None


def _normalize_recommendation(
    raw_result: dict[str, Any], fallback: dict[str, Any], plants: list[dict[str, Any]]
) -> dict[str, Any]:
    result = dict(raw_result)

    plant_id = _safe_text(result.get("plant_id"))
    plant = _plant_by_id(plants, plant_id)
    if plant is None:
        plant_id = _safe_text(fallback.get("plant_id"))
        plant = _plant_by_id(plants, plant_id)

    if plant is None:
        return fallback

    fallback_goals = list(plant.get("starter_goals") or fallback.get("starter_goals") or [])

    normalized = {
        "personality_summary": _safe_text(result.get("personality_summary"))
        or _safe_text(fallback.get("personality_summary")),
        "concern_summary": _safe_text(result.get("concern_summary"))
        or _safe_text(fallback.get("concern_summary")),
        "plant_name": _safe_text(result.get("plant_name")) or _safe_text(plant.get("name")),
        "plant_id": _safe_text(plant.get("id")),
        "plant_emoji": _safe_text(result.get("plant_emoji")) or _safe_text(plant.get("emoji")),
        "plant_reason": _safe_text(result.get("plant_reason"))
        or f"{_safe_text(plant.get('symbol'))}의 의미가 지금의 고민과 잘 맞아요.",
        "plant_symbol": _safe_text(result.get("plant_symbol")) or _safe_text(plant.get("symbol")),
        "starter_goals": _ensure_three_goals(result.get("starter_goals"), fallback_goals),
        "message": _safe_text(result.get("message")) or _safe_text(fallback.get("message")),
    }

    if any(not normalized.get(key) for key in REQUIRED_RESULT_KEYS if key != "starter_goals"):
        return fallback

    return normalized


def load_plants(path: str = "plants.json") -> list[dict[str, Any]]:
    file_path = _resolve_path(path)
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return [p for p in data if isinstance(p, dict)]
    except Exception:
        pass

    return DEFAULT_PLANTS.copy()


def fallback_recommendation(user_profile: dict[str, Any], plants: list[dict[str, Any]]) -> dict[str, Any]:
    usable_plants = plants if plants else DEFAULT_PLANTS.copy()

    best_plant = max(usable_plants, key=lambda p: _score_plant(p, user_profile))
    concern_type = _safe_text(user_profile.get("concern_type")).lower()
    survey_answers = user_profile.get("survey_answers") or {}

    result = {
        "personality_summary": _get_personality_summary(survey_answers),
        "concern_summary": _get_concern_summary(concern_type),
        "plant_name": _safe_text(best_plant.get("name")),
        "plant_id": _safe_text(best_plant.get("id")),
        "plant_emoji": _safe_text(best_plant.get("emoji")),
        "plant_reason": (
            f"{_safe_text(best_plant.get('name'))}의 상징인 "
            f"{_safe_text(best_plant.get('symbol'))}이(가) 지금의 고민을 작은 실천으로 바꾸는 데 잘 맞아요."
        ),
        "plant_symbol": _safe_text(best_plant.get("symbol")),
        "starter_goals": _ensure_three_goals(
            best_plant.get("starter_goals"),
            [
                "오늘 할 수 있는 10분 목표 1개 정하기",
                "시작 시간을 정하고 바로 1회 실행하기",
                "끝난 뒤 스스로에게 짧게 칭찬 남기기",
            ],
        ),
        "message": "오늘의 작은 실천이 내일의 자신감을 키워줘요. 지금 한 걸음만 시작해봐요.",
    }
    return result


def build_recommendation_prompt(user_profile: dict[str, Any], plants: list[dict[str, Any]]) -> str:
    persona = _get_persona(user_profile.get("concern_type"), user_profile.get("survey_answers"))
    compact_plants = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "emoji": p.get("emoji"),
            "keywords": p.get("keywords"),
            "concern_types": p.get("concern_types"),
            "symbol": p.get("symbol"),
            "description": p.get("description"),
            "starter_goals": p.get("starter_goals"),
        }
        for p in plants
    ]

    return (
        f"너는 청소년을 위한 '{persona['name']}'야. {persona['tone']}. {persona['focus']}. "
        "반드시 JSON 객체 하나만 출력해. 코드블록, 설명문, 추가 텍스트를 절대 출력하지 마.\n\n"
        "반환 JSON 키는 아래 9개를 정확히 사용해:\n"
        "personality_summary, concern_summary, plant_name, plant_id, plant_emoji, "
        "plant_reason, plant_symbol, starter_goals, message\n"
        "starter_goals는 길이 3의 문자열 배열이어야 해.\n"
        "의학적 진단처럼 보이는 표현 금지, 비난 금지, 짧고 따뜻한 표현 사용.\n\n"
        f"사용자 입력:\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}\n\n"
        f"식물 후보:\n{json.dumps(compact_plants, ensure_ascii=False, indent=2)}\n"
    )


def recommend_plant(user_profile: dict[str, Any], plants_path: str = "plants.json") -> dict[str, Any]:
    plants = load_plants(plants_path)
    fallback = fallback_recommendation(user_profile, plants)

    if not _get_api_key():
        return fallback

    try:
        persona = _get_persona(user_profile.get("concern_type"), user_profile.get("survey_answers"))
        system_prompt = (
            f"당신은 청소년의 작은 실천을 돕는 '{persona['name']}'입니다. {persona['tone']}. "
            "반드시 JSON 객체만 출력하고, 불필요한 텍스트를 절대 포함하지 마세요."
        )
        user_prompt = build_recommendation_prompt(user_profile, plants)

        raw_text = _clean_json_text(
            _chat_completion_text(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=700,
            )
        )
        raw_result = _parse_json_relaxed(raw_text)
        if not isinstance(raw_result, dict):
            return fallback

        return _normalize_recommendation(raw_result, fallback, plants)
    except Exception as exc:
        _log_ai_error("recommend_plant", exc)
        return fallback


def generate_encouragement(
    goal_text: str,
    plant_state: dict[str, Any],
    concern_type: str = "",
    survey_answers: dict[str, Any] | None = None,
) -> str:
    goal = _safe_text(goal_text) or "오늘 목표"
    plant_name = _safe_text(plant_state.get("plant_name")) or "식물 친구"
    plant_emoji = _safe_text(plant_state.get("plant_emoji")) or "🌱"

    if _get_api_key():
        try:
            persona = _get_persona(concern_type, survey_answers)
            text = _chat_completion_text(
                [
                    {
                        "role": "system",
                        "content": (
                            f"청소년에게 보여줄 1~2문장 응원 메시지를 '{persona['name']}' 페르소나로 생성해. {persona['tone']}. "
                            "따뜻하고 짧게, 비난 없이, 의학적 표현 없이 작성해."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"목표: {goal}\n"
                            f"식물 상태: {json.dumps(plant_state, ensure_ascii=False)}\n"
                            "조건: 결과는 한국어 텍스트만 출력"
                        ),
                    },
                ],
                temperature=0.7,
                max_tokens=180,
            )
            if text:
                return text
        except Exception as exc:
            _log_ai_error("generate_encouragement", exc)

    return (
        f"{plant_emoji} {plant_name}도 네 실천을 보고 자라고 있어요. "
        f"'{goal}'을(를) 해낸 오늘의 한 걸음이 정말 멋져요!"
    )


def generate_companion_reply(
    user_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    goal_history: list[str],
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    fallback = _fallback_companion_reply(
        user_text,
        recommendation,
        concern_type,
        survey_answers,
        completed_count,
        goal_history,
    )

    if not _get_api_key():
        return fallback

    persona = _get_persona(concern_type, survey_answers)
    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    concern_label = _concern_label(concern_type)
    trait_text = _survey_trait_summary(survey_answers)
    goals = [str(g).strip() for g in recommendation.get("starter_goals", []) if str(g).strip()]
    recent_goals = [str(goal).strip() for goal in goal_history[-5:] if str(goal).strip()]
    recent_chat = []
    for entry in (chat_history or [])[-6:]:
        if not isinstance(entry, dict):
            continue
        role = _safe_text(entry.get("role")) or "assistant"
        content = _safe_text(entry.get("content"))
        if content:
            recent_chat.append({"role": role, "content": content})

    try:
        text = _chat_completion_text(
            [
                {
                    "role": "system",
                    "content": (
                        f"너는 청소년을 위한 따뜻한 식물 친구이자 '{persona['name']}'야. {persona['tone']}. {persona['focus']}. "
                        "평소엔 한국어로 1~3문장만 짧게 답하고, 실천 가능한 작은 다음 행동을 우선 제안해. "
                        "사용자의 최근 맥락과 목표 이력을 기억해서 자연스럽게 답하되, 비난, 진단, 과장된 약속은 하지 마. "
                        "사용자가 목표를 말하거나 목표 추천을 원하면, 그 목표를 5~15분 안에 할 수 있는 아주 작은 단계 2~3개로 나눠서 "
                        "1) 2) 3) 번호 목록으로 짧게 제시해. 각 단계는 한 문장으로 구체적이고 바로 실행할 수 있게 써. "
                        "사용자가 오늘 하고 싶은 일이나 해야 할 일을 이야기했지만 아직 '오늘의 목표에 넣어줘'처럼 목표 추가를 정확히 요청하지 않았다면, "
                        "단계로 나누지 말고 먼저 짧게 공감한 뒤 '오늘의 목표에 넣어줘'라고 말해주면 작은 목표로 나눠서 넣어주겠다고 자연스럽게 안내해. "
                        "응원을 원할 때는 목표를 나누지 말고 짧고 다정하게 격려해. "
                        "응답은 일반 텍스트만 출력해."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"식물 이름: {plant_name}\n"
                        f"고민 유형: {concern_label}\n"
                        f"설문 성향 요약: {trait_text}\n"
                        f"완료 횟수: {max(0, int(completed_count))}\n"
                        f"추천 시작 목표: {json.dumps(goals, ensure_ascii=False)}\n"
                        f"최근 완료 목표: {json.dumps(recent_goals, ensure_ascii=False)}\n"
                        f"최근 대화: {json.dumps(recent_chat, ensure_ascii=False)}\n"
                        f"사용자 메시지: {user_text}\n"
                        "조건: 필요하면 최근 완료 목표를 자연스럽게 언급하고, 답변 끝에는 다음에 바로 할 수 있는 작은 행동을 한 가지 포함해."
                    ),
                },
            ],
            temperature=0.7,
            max_tokens=320,
        )
        if text:
            return text
    except Exception as exc:
        _log_ai_error("generate_companion_reply", exc)

    return fallback


def _fallback_goal_options(user_text: str, recommendation: dict[str, Any], goal_history: list[str]) -> list[str]:
    goals = [str(g).strip() for g in recommendation.get("starter_goals", []) if str(g).strip()]
    done_set = {g.strip() for g in goal_history if g and g.strip()}
    remaining = [g for g in goals if g not in done_set]
    base_fallback = remaining or goals

    context_text = _safe_text(user_text)
    if context_text:
        return _ensure_three_goals(_split_goal_into_small_steps(context_text), base_fallback)

    return _ensure_three_goals(base_fallback, base_fallback)


def generate_goal_options(
    user_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    goal_history: list[str],
    chat_history: list[dict[str, str]] | None = None,
) -> list[str]:
    fallback = _fallback_goal_options(user_text, recommendation, goal_history)

    if not _get_api_key():
        return fallback

    persona = _get_persona(concern_type, survey_answers)
    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    concern_label = _concern_label(concern_type)
    trait_text = _survey_trait_summary(survey_answers)
    recent_goals = [str(goal).strip() for goal in goal_history[-5:] if str(goal).strip()]
    recent_chat = []
    for entry in (chat_history or [])[-6:]:
        if not isinstance(entry, dict):
            continue
        role = _safe_text(entry.get("role")) or "assistant"
        content = _safe_text(entry.get("content"))
        if content:
            recent_chat.append({"role": role, "content": content})

    try:
        raw_text = _clean_json_text(
            _chat_completion_text(
                [
                    {
                        "role": "system",
                        "content": (
                            f"너는 청소년을 위한 '{persona['name']}'야. {persona['tone']}. {persona['focus']}. "
                            "사용자 메시지와 맥락을 참고해 오늘 바로 실행할 수 있는 아주 작은 목표 3개를 추천해. "
                            "각 목표는 5~15분 안에 끝낼 수 있는 구체적인 행동 한 문장이어야 해. "
                            "3개는 실제로 실행해야 할 순서대로 배열해. 배열의 첫 번째가 가장 먼저 할 일이야. "
                            "반드시 문자열 3개로 이루어진 JSON 배열만 출력해. 다른 설명이나 텍스트는 절대 출력하지 마."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"식물 이름: {plant_name}\n"
                            f"고민 유형: {concern_label}\n"
                            f"설문 성향 요약: {trait_text}\n"
                            f"완료 횟수: {max(0, int(completed_count))}\n"
                            f"추천 시작 목표: {json.dumps(fallback, ensure_ascii=False)}\n"
                            f"최근 완료 목표: {json.dumps(recent_goals, ensure_ascii=False)}\n"
                            f"최근 대화: {json.dumps(recent_chat, ensure_ascii=False)}\n"
                            f"사용자 메시지: {user_text}\n"
                        ),
                    },
                ],
                temperature=0.6,
                max_tokens=300,
            )
        )
        parsed = _parse_json_relaxed(raw_text)
        return _ensure_three_goals(parsed, fallback)
    except Exception as exc:
        _log_ai_error("generate_goal_options", exc)
        return fallback


def _fallback_watering_reply(worry_text: str, recommendation: dict[str, Any], completed_count: int) -> str:
    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    worry = _safe_text(worry_text) or "오늘의 고민"
    next_count = max(0, int(completed_count)) + 1
    return (
        f"'{worry}', 그 마음 잘 들었어. 그런 하루에도 목표를 해낸 건 진짜 대단한 거야. "
        f"{plant_name}가 그 마음을 물처럼 머금고 자라고 있어. "
        f"다음에 또 물을 주러 오면, {plant_name}가 조금 더 자란 모습을 보여줄게."
    )


def generate_watering_reply(
    worry_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    fallback = _fallback_watering_reply(worry_text, recommendation, completed_count)

    if not _get_api_key():
        return fallback

    persona = _get_persona(concern_type, survey_answers)
    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    concern_label = _concern_label(concern_type)
    trait_text = _survey_trait_summary(survey_answers)
    recent_chat = []
    for entry in (chat_history or [])[-6:]:
        if not isinstance(entry, dict):
            continue
        role = _safe_text(entry.get("role")) or "assistant"
        content = _safe_text(entry.get("content"))
        if content:
            recent_chat.append({"role": role, "content": content})

    try:
        text = _chat_completion_text(
            [
                {
                    "role": "system",
                    "content": (
                        f"너는 청소년의 마음을 들어주는 '{persona['name']}'이자 식물 친구야. {persona['tone']}. "
                        "사용자가 방금 나눈 고민을 판단하거나 바로 해결하려 하지 말고, 먼저 있는 그대로 공감하며 "
                        "그 마음을 짧게 되짚어줘서 '정말 듣고 있다'는 느낌을 줘. "
                        "그다음, 이런 마음이 드는 날에도 오늘 목표를 해낸 것 자체가 이미 의미 있는 실천이었다는 걸 짚어주고, "
                        "식물이 자라는 모습을 함께 지켜보고 싶다는 다정한 기대로 마무리해. "
                        "2~4문장, 한국어, 비난·진단·과장된 약속 금지. 응답은 일반 텍스트만 출력해."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"식물 이름: {plant_name}\n"
                        f"고민 유형: {concern_label}\n"
                        f"설문 성향 요약: {trait_text}\n"
                        f"완료 횟수: {max(0, int(completed_count))}\n"
                        f"최근 대화: {json.dumps(recent_chat, ensure_ascii=False)}\n"
                        f"방금 나눈 오늘의 고민: {worry_text}\n"
                    ),
                },
            ],
            temperature=0.7,
            max_tokens=220,
        )
        if text:
            return text
    except Exception as exc:
        _log_ai_error("generate_watering_reply", exc)

    return fallback


def generate_goal_breakdown(
    goal_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    chat_history: list[dict[str, str]] | None = None,
) -> list[str]:
    fallback = _split_goal_into_small_steps(goal_text)

    if not _get_api_key():
        return fallback

    persona = _get_persona(concern_type, survey_answers)
    plant_name = _safe_text(recommendation.get("plant_name")) or "식물 친구"
    concern_label = _concern_label(concern_type)
    trait_text = _survey_trait_summary(survey_answers)
    recent_chat = []
    for entry in (chat_history or [])[-6:]:
        if not isinstance(entry, dict):
            continue
        role = _safe_text(entry.get("role")) or "assistant"
        content = _safe_text(entry.get("content"))
        if content:
            recent_chat.append({"role": role, "content": content})

    try:
        raw_text = _clean_json_text(
            _chat_completion_text(
                [
                    {
                        "role": "system",
                        "content": (
                            f"너는 청소년을 위한 '{persona['name']}'야. {persona['tone']}. {persona['focus']}. "
                            "사용자가 고른 목표 하나를 5~15분 안에 끝낼 수 있는 아주 작은 실행 단계 3개로 쪼개. "
                            "순서대로 실행하면 원래 목표가 끝나도록, 각 단계는 구체적인 행동 한 문장이어야 해. "
                            "배열의 순서는 실제로 실행해야 할 순서와 정확히 같아야 해. 첫 번째가 가장 먼저 할 일이야. "
                            "반드시 문자열 3개로 이루어진 JSON 배열만 출력해. 다른 설명이나 텍스트는 절대 출력하지 마."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"쪼갤 목표: {goal_text}\n"
                            f"식물 이름: {plant_name}\n"
                            f"고민 유형: {concern_label}\n"
                            f"설문 성향 요약: {trait_text}\n"
                            f"완료 횟수: {max(0, int(completed_count))}\n"
                            f"최근 대화: {json.dumps(recent_chat, ensure_ascii=False)}\n"
                        ),
                    },
                ],
                temperature=0.5,
                max_tokens=260,
            )
        )
        parsed = _parse_json_relaxed(raw_text)
        return _ensure_three_goals(parsed, fallback)
    except Exception as exc:
        _log_ai_error("generate_goal_breakdown", exc)
        return fallback
