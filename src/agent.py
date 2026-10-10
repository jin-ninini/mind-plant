from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

import ai
from growth import get_growth_stage, get_next_stage_preview

MAX_STEPS = 4
MAX_GOAL_OPTIONS = 8
MAX_MEMORY_NOTES = 10

# 식물 친구가 대화 중에 스스로 골라 호출할 수 있는 도구 목록입니다(OpenAI tool calling 형식).
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "사용자의 목표 완료 횟수, 현재 성장 단계, 다음 단계까지 남은 횟수, 오늘의 목표 목록을 조회한다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_goal_history",
            "description": "사용자가 최근에 완료한 목표 목록을 조회한다. 예전에 무엇을 해냈는지 언급하거나 다음 목표를 고를 때 사용한다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_today_goals",
            "description": (
                "오늘의 목표 목록을 설정한다. 사용자가 목표 추가를 요청하거나 제안에 동의했을 때만 호출한다. "
                "각 목표는 5~15분 안에 끝낼 수 있는 구체적인 한 문장으로 쓴다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추가할 작은 목표 1~5개",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["replace", "append"],
                        "description": "replace는 기존 목록을 교체하고, append는 기존 목록 뒤에 추가한다.",
                    },
                },
                "required": ["goals", "mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_today_goal",
            "description": "오늘의 목표 목록 중 지금 바로 시작할 목표 하나를 선택한다. 목록에 있는 문장을 그대로 넘긴다.",
            "parameters": {
                "type": "object",
                "properties": {"goal": {"type": "string"}},
                "required": ["goal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": (
                "다음 대화에도 도움이 될 사용자 정보를 장기 기억에 저장한다. "
                "예: 시험 일정, 좋아하는 공부 방식, 자주 막히는 상황. 연락처나 주소 같은 개인정보는 저장하지 않는다."
            ),
            "parameters": {
                "type": "object",
                "properties": {"note": {"type": "string", "description": "한 문장으로 요약한 기억"}},
                "required": ["note"],
            },
        },
    },
]


@dataclass
class AgentState:
    completed_count: int
    goal_history: list[str]
    goal_options: list[str]
    today_goal: str
    memory_notes: list[str]
    actions: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    reply: str
    goal_options: list[str]
    today_goal: str
    memory_notes: list[str]
    actions: list[str]


Completer = Callable[[list[dict[str, Any]], "list[dict[str, Any]] | None"], Any]


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        text = ai._safe_text(value)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _tool_get_progress(state: AgentState, _args: dict[str, Any]) -> dict[str, Any]:
    stage = get_growth_stage(state.completed_count)
    preview = get_next_stage_preview(state.completed_count)
    state.actions.append("진행 상황 확인")
    return {
        "completed_count": state.completed_count,
        "stage": stage["stage"],
        "level": stage["level"],
        "next_stage": preview["stage"] if preview else None,
        "remaining_to_next_stage": preview["remaining"] if preview else 0,
        "today_goals": state.goal_options,
        "selected_goal": state.today_goal,
    }


def _tool_get_goal_history(state: AgentState, _args: dict[str, Any]) -> dict[str, Any]:
    state.actions.append("완료 기록 확인")
    return {"recent_completed_goals": state.goal_history[-10:]}


def _tool_set_today_goals(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    goals = _clean_list(args.get("goals"))[:5]
    if not goals:
        return {"ok": False, "error": "goals가 비어 있어요."}

    base = state.goal_options if args.get("mode") == "append" else []
    merged = _clean_list(base + goals)[:MAX_GOAL_OPTIONS]
    state.goal_options = merged
    if state.today_goal not in merged:
        state.today_goal = merged[0]
    state.actions.append(f"오늘의 목표 {len(goals)}개 설정")
    return {"ok": True, "today_goals": merged, "selected_goal": state.today_goal}


def _tool_select_today_goal(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    goal = ai._safe_text(args.get("goal"))
    if goal not in state.goal_options:
        return {"ok": False, "error": "오늘의 목표 목록에 없는 목표예요.", "today_goals": state.goal_options}
    state.today_goal = goal
    state.actions.append("시작할 목표 선택")
    return {"ok": True, "selected_goal": goal}


def _tool_remember(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    note = ai._safe_text(args.get("note"))[:120]
    if not note:
        return {"ok": False, "error": "note가 비어 있어요."}
    if note not in state.memory_notes:
        state.memory_notes = (state.memory_notes + [note])[-MAX_MEMORY_NOTES:]
    state.actions.append("기억 저장")
    return {"ok": True, "memory_notes": state.memory_notes}


TOOL_HANDLERS: dict[str, Callable[[AgentState, dict[str, Any]], dict[str, Any]]] = {
    "get_progress": _tool_get_progress,
    "get_goal_history": _tool_get_goal_history,
    "set_today_goals": _tool_set_today_goals,
    "select_today_goal": _tool_select_today_goal,
    "remember": _tool_remember,
}


def execute_tool(state: AgentState, name: str, raw_arguments: str) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"ok": False, "error": f"알 수 없는 도구: {name}"}
    try:
        args = json.loads(raw_arguments or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "arguments가 올바른 JSON이 아니에요."}
    if not isinstance(args, dict):
        args = {}
    return handler(state, args)


def _build_system_prompt(
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    memory_notes: list[str],
) -> str:
    persona = ai._get_persona(concern_type, survey_answers)
    plant_name = ai._safe_text(recommendation.get("plant_name")) or "식물 친구"
    memory_text = "\n".join(f"- {note}" for note in memory_notes) or "- (아직 없음)"
    return (
        f"너는 청소년을 위한 따뜻한 식물 친구 '{plant_name}'이자 '{persona['name']}'야. {persona['tone']}. {persona['focus']}.\n"
        f"고민 유형: {ai._concern_label(concern_type)} / 설문 성향: {ai._survey_trait_summary(survey_answers)}\n"
        "너는 도구를 써서 사용자의 목표 실천을 직접 도와주는 에이전트야.\n"
        "- 진행 상황이나 과거 기록이 필요하면 추측하지 말고 get_progress, get_goal_history를 호출해.\n"
        "- 사용자가 목표 추가를 요청하거나 네 제안에 동의하면 set_today_goals로 5~15분짜리 작은 목표 2~3개를 넣어.\n"
        "- 요청이 없는데 목표를 마음대로 넣지 말고, 먼저 공감한 뒤 넣어줄지 물어봐.\n"
        "- 다음 대화에도 쓸모 있는 사실(시험 일정, 선호하는 방식 등)을 알게 되면 remember로 저장해.\n"
        "- 최종 답변은 한국어 1~3문장, 일반 텍스트로 짧게 하고 끝에 바로 할 수 있는 작은 행동 하나를 제안해.\n"
        "- 비난, 진단, 과장된 약속은 하지 마. 자해나 위험 신호가 보이면 믿을 수 있는 어른이나 청소년상담 1388에 도움을 요청하도록 안내해.\n"
        f"장기 기억:\n{memory_text}"
    )


def _default_completer(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> Any:
    client, model = ai._make_client()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_completion_tokens": 512,
    }
    if tools:
        kwargs["tools"] = tools
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message


def _finish(state: AgentState, text: Any) -> AgentResult | None:
    reply = ai._safe_text(text)
    if not reply:
        return None
    return AgentResult(
        reply=reply,
        goal_options=state.goal_options,
        today_goal=state.today_goal,
        memory_notes=state.memory_notes,
        actions=state.actions,
    )


def run_companion_agent(
    user_text: str,
    *,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    goal_history: list[str],
    chat_history: list[dict[str, str]],
    goal_options: list[str],
    today_goal: str,
    memory_notes: list[str],
    complete: Completer | None = None,
) -> AgentResult | None:
    """LLM이 도구를 골라 호출하고 결과를 보며 답하는 루프입니다. 실패하면 None을 돌려 기존 흐름으로 넘깁니다."""
    if complete is None:
        if not ai._get_api_key():
            return None
        complete = _default_completer

    state = AgentState(
        completed_count=max(0, int(completed_count)),
        goal_history=_clean_list(goal_history),
        goal_options=_clean_list(goal_options),
        today_goal=ai._safe_text(today_goal),
        memory_notes=_clean_list(memory_notes),
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_system_prompt(recommendation, concern_type, survey_answers, state.memory_notes)}
    ]
    for entry in chat_history[-8:]:
        content = ai._safe_text(entry.get("content"))
        if content:
            role = "user" if entry.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    try:
        for _ in range(MAX_STEPS):
            message = complete(messages, TOOLS)
            tool_calls = list(getattr(message, "tool_calls", None) or [])
            if not tool_calls:
                return _finish(state, getattr(message, "content", ""))

            messages.append(
                {
                    "role": "assistant",
                    "content": getattr(message, "content", None) or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {"name": call.function.name, "arguments": call.function.arguments},
                        }
                        for call in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                result = execute_tool(state, call.function.name, call.function.arguments)
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)}
                )

        # 단계 제한에 도달하면 도구 없이 최종 답변만 받습니다.
        message = complete(messages, None)
        return _finish(state, getattr(message, "content", ""))
    except Exception as exc:
        ai._log_ai_error("run_companion_agent", exc)
        return None
