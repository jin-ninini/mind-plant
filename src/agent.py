from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

import ai
from growth import get_growth_stage, get_next_stage_preview

MAX_STEPS = 5
MAX_GOAL_OPTIONS = 8
MAX_GOAL_LENGTH = 80
MAX_MEMORY_NOTES = 10

# 위기 신호는 LLM 판단에 맡기지 않고 코드에서 먼저 걸러 고정된 안내로 답합니다.
CRISIS_PATTERNS = re.compile(
    r"죽고\s*싶|자살|자해|극단적\s*(인\s*)?선택|사라지고\s*싶|살기\s*싫|살고\s*싶지\s*않|"
    r"목숨을?\s*끊|뛰어내리|손목을?\s*긋|없어지고\s*싶|죽어\s*버리"
)
CRISIS_REPLY = (
    "그 말을 해줘서 정말 고마워. 지금 많이 힘든 것 같아서, 이건 나 혼자 들어주기보다 꼭 사람의 도움이 필요해. "
    "지금 바로 청소년상담 1388(전화·문자·카카오톡)이나 자살예방상담전화 109에 연락해 줘. 24시간 언제든 받아줘. "
    "위급하면 112나 119에 바로 연락하고, 믿을 수 있는 어른에게도 지금 마음을 꼭 말해줘. 너는 소중한 사람이야."
)

# 장기 기억에 연락처나 주민번호 같은 개인정보가 저장되지 않도록 막습니다.
PII_PATTERNS = re.compile(r"\d{2,3}-?\d{3,4}-?\d{4}|[\w.+-]+@[\w-]+\.[\w.]+|\d{6}-?[1-4]\d{6}")
DATE_PREFIX = re.compile(r"^\(\d{4}-\d{2}-\d{2}\)\s*")

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
            "name": "break_down_goal",
            "description": (
                "오늘의 목표 하나가 너무 크거나 사용자가 막막해할 때, 그 목표를 더 작은 단계로 나눠 목록에서 교체한다. "
                "각 단계는 5분 안팎으로 끝낼 수 있는 구체적인 행동으로 쓴다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "나눌 목표(오늘의 목표 목록에 있는 문장 그대로)"},
                    "steps": {"type": "array", "items": {"type": "string"}, "description": "작은 단계 2~4개"},
                },
                "required": ["goal", "steps"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_goal_completion",
            "description": (
                "사용자가 오늘의 목표 중 하나를 '다 했다'고 분명히 말했을 때만 호출한다. "
                "목표 마무리 대화와 물주기 화면으로 안내하며, 식물 성장은 사용자가 물주기를 마쳐야 반영된다. "
                "하는 중이거나 할 예정이라는 말에는 호출하지 않는다."
            ),
            "parameters": {
                "type": "object",
                "properties": {"goal": {"type": "string", "description": "완료한 목표(오늘의 목표 목록에 있는 문장 그대로)"}},
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
    {
        "type": "function",
        "function": {
            "name": "forget_memory",
            "description": (
                "장기 기억 중 더 이상 맞지 않거나 사용자가 지워 달라고 한 기억을 삭제한다. "
                "정보가 바뀐 경우에는 삭제한 뒤 remember로 새 내용을 저장한다."
            ),
            "parameters": {
                "type": "object",
                "properties": {"note": {"type": "string", "description": "삭제할 기억 문장(장기 기억 목록에 있는 문장 그대로)"}},
                "required": ["note"],
            },
        },
    },
]

# 선제적 체크인에서는 상태를 바꾸지 않는 조회 도구만 허용합니다.
READ_ONLY_TOOL_NAMES = {"get_progress", "get_goal_history"}
READ_ONLY_TOOLS = [tool for tool in TOOLS if tool["function"]["name"] in READ_ONLY_TOOL_NAMES]


@dataclass
class AgentState:
    completed_count: int
    goal_history: list[str]
    goal_options: list[str]
    today_goal: str
    memory_notes: list[str]
    today: str = ""
    pending_completion: str = ""
    actions: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentResult:
    reply: str
    goal_options: list[str]
    today_goal: str
    memory_notes: list[str]
    actions: list[str]
    pending_completion: str = ""
    trace: list[dict[str, Any]] = field(default_factory=list)
    guardrail: str = ""


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
    goals = [g[:MAX_GOAL_LENGTH] for g in _clean_list(args.get("goals"))[:5]]
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


def _tool_break_down_goal(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    goal = ai._safe_text(args.get("goal"))
    if goal not in state.goal_options:
        return {"ok": False, "error": "오늘의 목표 목록에 없는 목표예요.", "today_goals": state.goal_options}
    steps = [s[:MAX_GOAL_LENGTH] for s in _clean_list(args.get("steps"))[:4]]
    if len(steps) < 2:
        return {"ok": False, "error": "steps는 2개 이상이어야 해요."}

    # 원래 목표 자리에 작은 단계들을 끼워 넣습니다.
    idx = state.goal_options.index(goal)
    others = [g for g in state.goal_options if g != goal]
    merged = _clean_list(others[:idx] + steps + others[idx:])[:MAX_GOAL_OPTIONS]
    state.goal_options = merged
    if state.today_goal == goal or state.today_goal not in merged:
        state.today_goal = merged[idx] if idx < len(merged) else merged[0]
    state.actions.append("목표 잘게 나누기")
    return {"ok": True, "today_goals": merged, "selected_goal": state.today_goal}


def _tool_start_goal_completion(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    goal = ai._safe_text(args.get("goal"))
    if goal not in state.goal_options:
        return {"ok": False, "error": "오늘의 목표 목록에 없는 목표예요.", "today_goals": state.goal_options}
    # 성장 횟수는 여기서 올리지 않습니다. 사용자가 마무리 대화와 물주기를 마쳐야 반영됩니다.
    state.pending_completion = goal
    state.today_goal = goal
    state.actions.append("목표 완료 처리 시작")
    return {
        "ok": True,
        "goal": goal,
        "next": "답변 뒤 사용자는 마무리 대화와 물주기 화면으로 이동한다. 축하하고 소감을 들려 달라고 짧게 안내해.",
    }


def _tool_remember(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    note = ai._safe_text(args.get("note"))[:120]
    if not note:
        return {"ok": False, "error": "note가 비어 있어요."}
    if PII_PATTERNS.search(note):
        return {"ok": False, "error": "연락처나 주민번호 같은 개인정보는 기억에 저장할 수 없어요."}
    core = _strip_date(note).rstrip(".")
    for existing in state.memory_notes:
        existing_core = _strip_date(existing).rstrip(".")
        if core in existing_core or existing_core in core:
            return {"ok": False, "error": "이미 비슷한 기억이 있어요. 내용이 바뀌었다면 forget_memory 후 저장하세요.", "existing": existing}
    # 날짜를 붙여 두면 다음 체크인에서 "어제 말한 시험"처럼 시점을 짚을 수 있습니다.
    if state.today:
        note = f"({state.today}) {note}"
    if note not in state.memory_notes:
        state.memory_notes = (state.memory_notes + [note])[-MAX_MEMORY_NOTES:]
    state.actions.append("기억 저장")
    return {"ok": True, "memory_notes": state.memory_notes}


def _strip_date(note: str) -> str:
    return DATE_PREFIX.sub("", note).strip()


def _tool_forget_memory(state: AgentState, args: dict[str, Any]) -> dict[str, Any]:
    # 번호로 고르게 하면 LLM이 엉뚱한 기억을 지우는 일이 있어, 문장 내용으로 정확히 하나를 찾습니다.
    target = _strip_date(ai._safe_text(args.get("note")))
    if not target:
        return {"ok": False, "error": "note가 비어 있어요."}
    matches = [n for n in state.memory_notes if _strip_date(n) == target]
    if not matches:
        matches = [n for n in state.memory_notes if target in n]
    if len(matches) != 1:
        reason = "일치하는 기억이 없어요." if not matches else "여러 기억과 겹쳐요. 문장을 그대로 넘겨주세요."
        return {"ok": False, "error": reason, "memory_notes": state.memory_notes}
    removed = matches[0]
    state.memory_notes = [n for n in state.memory_notes if n != removed]
    state.actions.append("기억 삭제")
    return {"ok": True, "removed": removed, "memory_notes": state.memory_notes}


TOOL_HANDLERS: dict[str, Callable[[AgentState, dict[str, Any]], dict[str, Any]]] = {
    "get_progress": _tool_get_progress,
    "get_goal_history": _tool_get_goal_history,
    "set_today_goals": _tool_set_today_goals,
    "select_today_goal": _tool_select_today_goal,
    "break_down_goal": _tool_break_down_goal,
    "start_goal_completion": _tool_start_goal_completion,
    "remember": _tool_remember,
    "forget_memory": _tool_forget_memory,
}


def detect_crisis(text: str) -> bool:
    return bool(CRISIS_PATTERNS.search(ai._safe_text(text)))


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
    today: str = "",
) -> str:
    persona = ai._get_persona(concern_type, survey_answers)
    plant_name = ai._safe_text(recommendation.get("plant_name")) or "식물 친구"
    memory_text = "\n".join(f"- {note}" for note in memory_notes) or "- (아직 없음)"
    today_line = f"오늘 날짜: {today}\n" if today else ""
    return (
        f"너는 청소년을 위한 따뜻한 식물 친구 '{plant_name}'이자 '{persona['name']}'야. {persona['tone']}. {persona['focus']}.\n"
        f"고민 유형: {ai._concern_label(concern_type)} / 설문 성향: {ai._survey_trait_summary(survey_answers)}\n"
        f"{today_line}"
        "너는 도구를 써서 사용자의 목표 실천을 직접 도와주는 에이전트야.\n"
        "- 진행 상황이나 과거 기록이 필요하면 추측하지 말고 get_progress, get_goal_history를 호출해.\n"
        "- 사용자가 목표 추가를 요청하거나 네 제안에 동의하면 set_today_goals로 5~15분짜리 작은 목표 2~3개를 넣어.\n"
        "- 요청이 없는데 목표를 마음대로 넣지 말고, 먼저 공감한 뒤 넣어줄지 물어봐.\n"
        "- 사용자가 목표가 막막하다고 하면 break_down_goal로 더 작은 단계로 나눠.\n"
        "- 사용자가 오늘의 목표를 '다 했다'고 분명히 말하면 start_goal_completion을 호출해. 할 예정이라는 말에는 호출하지 마.\n"
        "- 다음 대화에도 쓸모 있는 사실(시험 일정, 선호하는 방식 등)을 알게 되면 remember로 저장해.\n"
        "- 기억이 틀렸거나 바뀌었거나 지워 달라고 하면 forget_memory로 지우고, 필요하면 remember로 새로 저장해.\n"
        "- 도구가 ok:false를 돌려주면 이유를 보고 고쳐서 다시 시도하거나 사용자에게 확인해.\n"
        "- 저장, 설정, 삭제처럼 상태를 바꾸는 일은 이번 차례에 실제로 도구를 호출해 성공한 것만 했다고 말해. 하지 않은 일을 했다고 말하지 마.\n"
        "- 완료 기록에는 날짜가 없으니 '어제', '지난주'처럼 언제 했는지 지어내지 마. 날짜는 장기 기억에 적힌 것만 써.\n"
        "- 최종 답변은 한국어 1~3문장, 일반 텍스트로 짧게 하고 끝에 바로 할 수 있는 작은 행동 하나를 제안해. 마크다운 기호는 쓰지 마.\n"
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


def _make_state(
    completed_count: int,
    goal_history: list[str],
    goal_options: list[str],
    today_goal: str,
    memory_notes: list[str],
    today: str,
) -> AgentState:
    return AgentState(
        completed_count=max(0, int(completed_count)),
        goal_history=_clean_list(goal_history),
        goal_options=_clean_list(goal_options),
        today_goal=ai._safe_text(today_goal),
        memory_notes=_clean_list(memory_notes),
        today=ai._safe_text(today),
    )


def _finish(state: AgentState, text: Any) -> AgentResult | None:
    reply = ai._safe_text(text)
    if not reply:
        return None
    state.trace.append({"type": "reply", "content": reply})
    return AgentResult(
        reply=reply,
        goal_options=state.goal_options,
        today_goal=state.today_goal,
        memory_notes=state.memory_notes,
        actions=state.actions,
        pending_completion=state.pending_completion,
        trace=state.trace,
    )


def _run_loop(
    state: AgentState,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    complete: Completer,
) -> AgentResult | None:
    allowed = {tool["function"]["name"] for tool in tools}
    for step in range(1, MAX_STEPS + 1):
        message = complete(messages, tools)
        tool_calls = list(getattr(message, "tool_calls", None) or [])
        if not tool_calls:
            return _finish(state, getattr(message, "content", ""))

        thought = ai._safe_text(getattr(message, "content", None))
        if thought:
            state.trace.append({"type": "thought", "step": step, "content": thought})
        messages.append(
            {
                "role": "assistant",
                "content": thought,
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
            name = call.function.name
            if name in allowed:
                result = execute_tool(state, name, call.function.arguments)
            else:
                result = {"ok": False, "error": f"지금은 사용할 수 없는 도구: {name}"}
            try:
                parsed_args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                parsed_args = call.function.arguments
            state.trace.append(
                {
                    "type": "tool",
                    "step": step,
                    "name": name,
                    "args": parsed_args,
                    "result": result,
                    "ok": result.get("ok", True) is not False,
                }
            )
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})

    # 단계 제한에 도달하면 도구 없이 최종 답변만 받습니다.
    state.trace.append({"type": "limit", "step": MAX_STEPS})
    message = complete(messages, None)
    return _finish(state, getattr(message, "content", ""))


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
    today: str = "",
    complete: Completer | None = None,
) -> AgentResult | None:
    """LLM이 도구를 골라 호출하고 결과를 보며 답하는 루프입니다. 실패하면 None을 돌려 기존 흐름으로 넘깁니다."""
    state = _make_state(completed_count, goal_history, goal_options, today_goal, memory_notes, today)

    # 가드레일은 API 키가 없어도 동작해야 하므로 LLM 호출보다 먼저 확인합니다.
    if detect_crisis(user_text):
        state.actions.append("안전 가드레일 작동")
        state.trace.append({"type": "guardrail", "content": "위기 표현 감지: LLM을 호출하지 않고 고정 안내로 응답"})
        result = _finish(state, CRISIS_REPLY)
        if result is not None:
            result.guardrail = "crisis"
        return result

    if complete is None:
        if not ai._get_api_key():
            return None
        complete = _default_completer

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": _build_system_prompt(recommendation, concern_type, survey_answers, state.memory_notes, state.today),
        }
    ]
    for entry in chat_history[-8:]:
        content = ai._safe_text(entry.get("content"))
        if content:
            role = "user" if entry.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    try:
        return _run_loop(state, messages, TOOLS, complete)
    except Exception as exc:
        ai._log_ai_error("run_companion_agent", exc)
        return None


def run_checkin_agent(
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
    today: str = "",
    last_visit: str = "",
    complete: Completer | None = None,
) -> AgentResult | None:
    """사용자가 그날 처음 들어왔을 때 기억과 진행 상황을 보고 식물 친구가 먼저 말을 겁니다."""
    if complete is None:
        if not ai._get_api_key():
            return None
        complete = _default_completer

    state = _make_state(completed_count, goal_history, goal_options, today_goal, memory_notes, today)
    instruction = (
        "[체크인] 사용자가 오늘 처음 접속했어. 사용자는 아직 아무 말도 하지 않았어. "
        f"마지막 방문일: {last_visit or '알 수 없음'}. "
        "필요하면 조회 도구로 진행 상황과 완료 기록을 확인하고, 장기 기억에 날짜가 지난 일정(시험, 발표 등)이 있으면 "
        "그 결과를 다정하게 물어봐. 없으면 지난번 흐름을 짧게 짚어 줘. "
        "1~2문장으로 먼저 말을 걸고, 오늘 할 수 있는 작은 행동 하나를 제안해."
    )
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": _build_system_prompt(recommendation, concern_type, survey_answers, state.memory_notes, state.today),
        }
    ]
    for entry in chat_history[-6:]:
        content = ai._safe_text(entry.get("content"))
        if content:
            role = "user" if entry.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": instruction})

    try:
        return _run_loop(state, messages, READ_ONLY_TOOLS, complete)
    except Exception as exc:
        ai._log_ai_error("run_checkin_agent", exc)
        return None
