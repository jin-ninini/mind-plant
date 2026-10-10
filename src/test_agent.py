from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from agent import AgentState, execute_tool, run_companion_agent


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

    def __call__(self, messages, tools):
        self.calls.append(list(messages))
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
        completer = ScriptedCompleter([looping] * 4 + [SimpleNamespace(content="정리해서 알려줄게.", tool_calls=None)])
        result = _run(completer)
        self.assertEqual(result.reply, "정리해서 알려줄게.")
        self.assertEqual(len(completer.calls), 5)

    def test_error_returns_none_for_fallback(self) -> None:
        def broken(messages, tools):
            raise RuntimeError("network down")

        self.assertIsNone(_run(broken))

    def test_empty_reply_returns_none(self) -> None:
        completer = ScriptedCompleter([SimpleNamespace(content="  ", tool_calls=None)])
        self.assertIsNone(_run(completer))


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

    def test_unknown_tool_and_bad_json(self) -> None:
        self.assertFalse(execute_tool(self._state(), "delete_everything", "{}")["ok"])
        self.assertFalse(execute_tool(self._state(), "remember", "not json")["ok"])


if __name__ == "__main__":
    unittest.main()
