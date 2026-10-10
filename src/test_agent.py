from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from agent import CRISIS_REPLY, MAX_STEPS, AgentState, execute_tool, run_checkin_agent, run_companion_agent


def _tool_call(call_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments, ensure_ascii=False)),
    )


class ScriptedCompleter:
    """미리 정해 둔 응답을 순서대로 돌려주는 가짜 LLM입니다."""

    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = list(responses)
        self.calls: list[list[dict]] = []
        self.tools_seen: list[list[str]] = []

    def __call__(self, messages, tools):
        self.calls.append(list(messages))
        self.tools_seen.append([t["function"]["name"] for t in tools or []])
        return self.responses.pop(0)


def _run(completer: ScriptedCompleter, **overrides):
    kwargs = dict(
        recommendation={"plant_name": "스투키", "plant_id": "stuckii"},
        concern_type="focus",
        survey_answers={},
        completed_count=2,
        goal_history=["25분 타이머로 한 과제만 하기"],
        chat_history=[{"role": "assistant", "content": "안녕!"}],
        goal_options=[],
        today_goal="",
        memory_notes=[],
        complete=completer,
    )
    kwargs.update(overrides)
    return run_companion_agent("다음 주 수학 시험이야. 오늘의 목표에 넣어줘", **kwargs)


class AgentLoopTests(unittest.TestCase):
    def test_tool_calls_update_state_and_return_reply(self) -> None:
        completer = ScriptedCompleter(
            [
                SimpleNamespace(
                    content=None,
                    tool_calls=[
                        _tool_call("c1", "remember", {"note": "다음 주에 수학 시험이 있음"}),
                        _tool_call("c2", "set_today_goals", {"goals": ["수학 오답 3개 다시 풀기", "공식 5개 써보기"], "mode": "replace"}),
                    ],
                ),
                SimpleNamespace(content="좋아, 오답 3개부터 시작해 보자!", tool_calls=None),
            ]
        )

        result = _run(completer)

        self.assertIsNotNone(result)
        self.assertEqual(result.reply, "좋아, 오답 3개부터 시작해 보자!")
        self.assertEqual(result.goal_options, ["수학 오답 3개 다시 풀기", "공식 5개 써보기"])
        self.assertEqual(result.today_goal, "수학 오답 3개 다시 풀기")
        self.assertEqual(result.memory_notes, ["다음 주에 수학 시험이 있음"])
        self.assertEqual(result.actions, ["기억 저장", "오늘의 목표 2개 설정"])

        # 두 번째 호출에는 도구 결과가 tool 메시지로 전달되어야 합니다.
        tool_messages = [m for m in completer.calls[1] if m["role"] == "tool"]
        self.assertEqual([m["tool_call_id"] for m in tool_messages], ["c1", "c2"])

    def test_plain_reply_without_tools(self) -> None:
        completer = ScriptedCompleter([SimpleNamespace(content="오늘도 와줘서 고마워.", tool_calls=None)])
        result = _run(completer, goal_options=["물 한 컵 마시기"], today_goal="물 한 컵 마시기")
        self.assertEqual(result.reply, "오늘도 와줘서 고마워.")
        self.assertEqual(result.goal_options, ["물 한 컵 마시기"])
        self.assertEqual(result.actions, [])

    def test_step_limit_forces_final_answer_without_tools(self) -> None:
        looping = SimpleNamespace(content=None, tool_calls=[_tool_call("c", "get_progress", {})])
        completer = ScriptedCompleter([looping] * MAX_STEPS + [SimpleNamespace(content="정리해서 알려줄게.", tool_calls=None)])
        result = _run(completer)
        self.assertEqual(result.reply, "정리해서 알려줄게.")
        self.assertEqual(len(completer.calls), MAX_STEPS + 1)
        self.assertEqual(result.trace[-2]["type"], "limit")

    def test_error_returns_none_for_fallback(self) -> None:
        def broken(messages, tools):
            raise RuntimeError("network down")

        self.assertIsNone(_run(broken))

    def test_empty_reply_returns_none(self) -> None:
        completer = ScriptedCompleter([SimpleNamespace(content="  ", tool_calls=None)])
        self.assertIsNone(_run(completer))

    def test_trace_records_tool_steps_and_reply(self) -> None:
        completer = ScriptedCompleter(
            [
                SimpleNamespace(content="먼저 진행 상황을 볼게.", tool_calls=[_tool_call("c1", "get_progress", {})]),
                SimpleNamespace(content="벌써 2번이나 해냈네!", tool_calls=None),
            ]
        )
        result = _run(completer)
        self.assertEqual([t["type"] for t in result.trace], ["thought", "tool", "reply"])
        self.assertEqual(result.trace[1]["name"], "get_progress")
        self.assertTrue(result.trace[1]["ok"])

    def test_goal_completion_is_handed_to_app_not_counted(self) -> None:
        completer = ScriptedCompleter(
            [
                SimpleNamespace(content=None, tool_calls=[_tool_call("c1", "start_goal_completion", {"goal": "공식 5개 써보기"})]),
                SimpleNamespace(content="와, 해냈구나! 소감 들려줘.", tool_calls=None),
            ]
        )
        result = _run(completer, goal_options=["공식 5개 써보기"], today_goal="")
        self.assertEqual(result.pending_completion, "공식 5개 써보기")
        self.assertEqual(result.today_goal, "공식 5개 써보기")


class GuardrailTests(unittest.TestCase):
    def test_crisis_text_skips_llm(self) -> None:
        def must_not_call(messages, tools):
            raise AssertionError("위기 표현에는 LLM을 호출하면 안 돼요")

        result = run_companion_agent(
            "요즘 너무 힘들어서 죽고 싶어",
            recommendation={},
            concern_type="focus",
            survey_answers={},
            completed_count=0,
            goal_history=[],
            chat_history=[],
            goal_options=[],
            today_goal="",
            memory_notes=[],
            complete=must_not_call,
        )
        self.assertEqual(result.reply, CRISIS_REPLY)
        self.assertEqual(result.guardrail, "crisis")
        self.assertIn("1388", result.reply)

    def test_ordinary_worry_is_not_flagged(self) -> None:
        completer = ScriptedCompleter([SimpleNamespace(content="그럴 수 있어.", tool_calls=None)])
        result = _run(completer)
        self.assertEqual(result.guardrail, "")

    def test_checkin_blocks_state_changing_tools(self) -> None:
        completer = ScriptedCompleter(
            [
                SimpleNamespace(
                    content=None,
                    tool_calls=[
                        _tool_call("c1", "get_goal_history", {}),
                        _tool_call("c2", "set_today_goals", {"goals": ["몰래 넣은 목표"], "mode": "replace"}),
                    ],
                ),
                SimpleNamespace(content="어제 수학 시험은 어땠어?", tool_calls=None),
            ]
        )
        result = run_checkin_agent(
            recommendation={"plant_name": "스투키"},
            concern_type="focus",
            survey_answers={},
            completed_count=1,
            goal_history=["공식 5개 써보기"],
            chat_history=[],
            goal_options=["A"],
            today_goal="A",
            memory_notes=["(2026-10-09) 내일 수학 시험이 있음"],
            today="2026-10-10",
            complete=completer,
        )
        self.assertEqual(result.reply, "어제 수학 시험은 어땠어?")
        self.assertEqual(result.goal_options, ["A"])
        blocked = [t for t in result.trace if t.get("name") == "set_today_goals"][0]
        self.assertFalse(blocked["ok"])
        # 체크인에는 조회 도구만 전달되어야 합니다.
        self.assertEqual(sorted(completer.tools_seen[0]), ["get_goal_history", "get_progress"])


class ToolTests(unittest.TestCase):
    def _state(self) -> AgentState:
        return AgentState(completed_count=3, goal_history=[], goal_options=["A", "B"], today_goal="A", memory_notes=[])

    def test_get_progress_reports_stage(self) -> None:
        result = execute_tool(self._state(), "get_progress", "{}")
        self.assertEqual(result["stage"], "어린잎")
        self.assertEqual(result["next_stage"], "줄기")
        self.assertEqual(result["remaining_to_next_stage"], 3)

    def test_append_goals_dedupes_and_keeps_selection(self) -> None:
        state = self._state()
        execute_tool(state, "set_today_goals", json.dumps({"goals": ["B", "C"], "mode": "append"}))
        self.assertEqual(state.goal_options, ["A", "B", "C"])
        self.assertEqual(state.today_goal, "A")

    def test_select_unknown_goal_is_rejected(self) -> None:
        state = self._state()
        result = execute_tool(state, "select_today_goal", json.dumps({"goal": "Z"}))
        self.assertFalse(result["ok"])
        self.assertEqual(state.today_goal, "A")

    def test_break_down_goal_replaces_in_place(self) -> None:
        state = self._state()
        result = execute_tool(state, "break_down_goal", json.dumps({"goal": "A", "steps": ["A-1", "A-2"]}))
        self.assertTrue(result["ok"])
        self.assertEqual(state.goal_options, ["A-1", "A-2", "B"])
        self.assertEqual(state.today_goal, "A-1")

    def test_break_down_goal_needs_two_steps(self) -> None:
        state = self._state()
        self.assertFalse(execute_tool(state, "break_down_goal", json.dumps({"goal": "A", "steps": ["A-1"]}))["ok"])
        self.assertEqual(state.goal_options, ["A", "B"])

    def test_completion_rejects_unknown_goal(self) -> None:
        state = self._state()
        self.assertFalse(execute_tool(state, "start_goal_completion", json.dumps({"goal": "Z"}))["ok"])
        self.assertEqual(state.pending_completion, "")

    def test_remember_adds_date_and_blocks_pii(self) -> None:
        state = self._state()
        state.today = "2026-10-10"
        execute_tool(state, "remember", json.dumps({"note": "아침형 인간"}))
        self.assertEqual(state.memory_notes, ["(2026-10-10) 아침형 인간"])
        result = execute_tool(state, "remember", json.dumps({"note": "엄마 번호는 010-1234-5678"}))
        self.assertFalse(result["ok"])
        self.assertEqual(len(state.memory_notes), 1)

    def test_remember_rejects_near_duplicate(self) -> None:
        state = self._state()
        state.memory_notes = ["(2026-10-10) 밤에 집중이 잘 되는 편"]
        result = execute_tool(state, "remember", json.dumps({"note": "사용자는 밤에 집중이 잘 되는 편이다."}))
        self.assertFalse(result["ok"])
        self.assertEqual(len(state.memory_notes), 1)

    def test_forget_memory_by_text(self) -> None:
        state = self._state()
        state.memory_notes = ["(2026-10-09) 수학 시험이 있음", "(2026-10-09) 아침형 인간", "영어를 좋아함"]
        # 날짜 접두어 없이 넘겨도 같은 기억을 찾아야 합니다.
        self.assertTrue(execute_tool(state, "forget_memory", json.dumps({"note": "아침형 인간"}))["ok"])
        self.assertEqual(state.memory_notes, ["(2026-10-09) 수학 시험이 있음", "영어를 좋아함"])
        self.assertFalse(execute_tool(state, "forget_memory", json.dumps({"note": "없는 기억"}))["ok"])

    def test_forget_memory_rejects_ambiguous_match(self) -> None:
        state = self._state()
        state.memory_notes = ["수학 시험 월요일", "수학 시험 범위 3단원"]
        self.assertFalse(execute_tool(state, "forget_memory", json.dumps({"note": "수학 시험"}))["ok"])
        self.assertEqual(len(state.memory_notes), 2)

    def test_unknown_tool_and_bad_json(self) -> None:
        self.assertFalse(execute_tool(self._state(), "delete_everything", "{}")["ok"])
        self.assertFalse(execute_tool(self._state(), "remember", "not json")["ok"])


if __name__ == "__main__":
    unittest.main()
