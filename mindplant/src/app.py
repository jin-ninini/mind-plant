from __future__ import annotations

import html
import io
import os
import random
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import streamlit as st
from dotenv import load_dotenv

from growth import build_plant_state
from storage import load_user_data, reset_user_data, save_user_data

load_dotenv()

st.set_page_config(page_title="MindPlant", page_icon="🌱", layout="centered")

if os.environ.get("MINDPLANT_TERMINAL_HELP_SHOWN") != "1":
    print("")
    print("========================================")
    print("MindPlant Streamlit server is running.")
    print("Open the Local URL shown above in your browser.")
    print("To stop the server, return to this terminal and press Ctrl+C.")
    print("========================================")
    print("")
    os.environ["MINDPLANT_TERMINAL_HELP_SHOWN"] = "1"

DATA_PATH = "data/demo_user.json"
PLANTS_PATH = "plants.json"
AVATAR_DIR = Path(__file__).resolve().parent.parent / "assets" / "plants"

CONCERN_OPTIONS = {
    "진로 고민": "career",
    "집중력 고민": "focus",
    "목표 실천 고민": "habit",
}


# ai.py import 실패 시에도 데모 화면이 계속 동작하도록 fallback을 제공합니다.
def _fallback_recommend_plant(user_profile: dict[str, Any], plants_path: str = "plants.json") -> dict[str, Any]:
    concern_type = str(user_profile.get("concern_type", "habit"))

    plant_map = {
        "career": {
            "plant_name": "해바라기",
            "plant_id": "sunflower",
            "plant_emoji": "🌻",
            "plant_symbol": "방향성, 희망, 꾸준함",
            "plant_reason": "진로 방향을 찾는 과정에 따뜻한 응원이 필요할 때 잘 어울려요.",
            "starter_goals": [
                "관심 직업 1개 찾아보기",
                "좋아하는 활동 3개 적기",
                "진로 영상 10분 보기",
            ],
            "concern_summary": "진로 방향을 정하는 데 고민이 있어요.",
        },
        "focus": {
            "plant_name": "선인장",
            "plant_id": "cactus",
            "plant_emoji": "🌵",
            "plant_symbol": "인내, 단단함, 몰입",
            "plant_reason": "짧은 몰입을 반복해 집중 흐름을 만들고 싶을 때 좋아요.",
            "starter_goals": [
                "25분 타이머로 한 과제 시작",
                "집중 시간에 알림 끄기",
                "끝난 뒤 5분 쉬고 1회 반복",
            ],
            "concern_summary": "집중 흐름이 자주 끊겨 고민이 있어요.",
        },
        "habit": {
            "plant_name": "바질",
            "plant_id": "basil",
            "plant_emoji": "🌿",
            "plant_symbol": "루틴, 성실함, 성장",
            "plant_reason": "작은 습관을 매일 이어가며 꾸준함을 키울 때 잘 맞아요.",
            "starter_goals": [
                "같은 시간에 15분 시작",
                "할 일 체크박스 3개 만들기",
                "잠들기 전 내일 목표 1개 정하기",
            ],
            "concern_summary": "목표 실천을 꾸준히 이어가는 게 고민이에요.",
        },
    }

    picked = plant_map.get(concern_type, plant_map["habit"])

    return {
        "personality_summary": "작은 단계를 쌓아갈 때 더 잘 성장하는 성향이에요.",
        "concern_summary": picked["concern_summary"],
        "plant_name": picked["plant_name"],
        "plant_id": picked["plant_id"],
        "plant_emoji": picked["plant_emoji"],
        "plant_reason": picked["plant_reason"],
        "plant_symbol": picked["plant_symbol"],
        "starter_goals": picked["starter_goals"],
        "message": "오늘의 작은 시작이 내일의 자신감을 만들어요.",
    }


def _fallback_generate_encouragement(goal_text: str, plant_state: dict[str, Any]) -> str:
    goal = goal_text.strip() if goal_text else "오늘 목표"
    plant_emoji = str(plant_state.get("plant_emoji", "🌱"))
    plant_name = str(plant_state.get("plant_name", "식물 친구"))
    return f"{plant_emoji} {plant_name}가 응원해요. '{goal}'을 해낸 너의 한 걸음이 정말 멋져요!"


def _fallback_generate_companion_reply(
    user_text: str,
    recommendation: dict[str, Any],
    concern_type: str,
    survey_answers: dict[str, Any],
    completed_count: int,
    goal_history: list[str],
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    del chat_history
    message = (user_text or "").strip()
    lowered = message.lower()

    plant_name = str(recommendation.get("plant_name", "식물 친구"))
    goals = [str(g).strip() for g in recommendation.get("starter_goals", []) if str(g).strip()]
    done_set = {g.strip() for g in goal_history if g and g.strip()}
    suggestion = next((g for g in goals if g not in done_set), goals[0] if goals else "오늘 10분만 집중해서 할 일 1개 정하기")

    if any(key in lowered for key in ["추천", "목표", "뭐할", "무엇", "해야"]):
        return f"{plant_name} 기준으로 지금은 '{suggestion}'을(를) 먼저 해보는 게 좋아요. 끝나면 바로 완료 눌러서 성장시켜봐요."

    if any(key in lowered for key in ["기억", "지난", "과거", "전에", "했었"]):
        if goal_history:
            recent = " / ".join(goal_history[-3:])
            return f"기억하고 있어요. 최근 완료한 목표는 {recent}예요. 다음엔 '{suggestion}' 어때요?"
        return f"아직 기록된 완료 목표가 없어요. 첫 목표로 '{suggestion}'부터 시작해볼까요?"

    if any(key in lowered for key in ["응원", "힘들", "지쳐", "불안", "걱정"]):
        return f"괜찮아요. {plant_name}도 작은 한 걸음을 좋아해요. 오늘은 10분만 투자해서 '{suggestion}'을(를) 해봐요."

    stage = build_plant_state(recommendation, completed_count)["growth_stage"]
    trait_text = _survey_trait_summary(survey_answers)
    concern_label = _concern_label(concern_type)
    return (
        f"지금은 {concern_label} 흐름이고 성향은 {trait_text}에 가까워요. "
        f"현재 단계는 {stage['stage']}이니 오늘 목표로 '{suggestion}'을(를) 추천할게요."
    )


def _load_ai_functions() -> tuple[Callable[..., dict[str, Any]], Callable[..., str], Callable[..., str], bool]:
    try:
        from ai import generate_companion_reply, generate_encouragement, recommend_plant

        return recommend_plant, generate_encouragement, generate_companion_reply, True
    except Exception:
        return _fallback_recommend_plant, _fallback_generate_encouragement, _fallback_generate_companion_reply, False


recommend_plant_fn, generate_encouragement_fn, generate_companion_reply_fn, ai_available = _load_ai_functions()


def _growth_level_from_count(completed_count: int) -> int:
    count = max(0, int(completed_count))
    if count == 0:
        return 1
    if count <= 2:
        return 2
    if count <= 4:
        return 3
    if count <= 7:
        return 4
    return 5


def _resolve_theme_tokens(completed_count: int) -> dict[str, str]:
    level = _growth_level_from_count(completed_count)
    palette = {
        1: {
            "bg_top": "#C7F5D3",
            "bg_mid": "#DFF8E6",
            "bg_bottom": "#F6FFDF",
            "accent": "#62D484",
            "accent_soft": "#9FE8AF",
            "chip": "#FFF6D3",
        },
        2: {
            "bg_top": "#B7F3DB",
            "bg_mid": "#D2F9EE",
            "bg_bottom": "#ECFFE6",
            "accent": "#50C6A6",
            "accent_soft": "#92E6CF",
            "chip": "#FFF5C3",
        },
        3: {
            "bg_top": "#B6EEEC",
            "bg_mid": "#D6F8F6",
            "bg_bottom": "#EEFEE8",
            "accent": "#49B1C8",
            "accent_soft": "#88D5E4",
            "chip": "#FFE6BF",
        },
        4: {
            "bg_top": "#BDE4FF",
            "bg_mid": "#D9EEFF",
            "bg_bottom": "#F2F7E8",
            "accent": "#5C8BFF",
            "accent_soft": "#9FB9FF",
            "chip": "#FFD9B3",
        },
        5: {
            "bg_top": "#FFDDBA",
            "bg_mid": "#FFEED4",
            "bg_bottom": "#FFF6DC",
            "accent": "#FF9B55",
            "accent_soft": "#FFC58E",
            "chip": "#FFEAA1",
        },
    }
    return palette.get(level, palette[1])


@lru_cache(maxsize=128)
def _avatar_asset_name(plant_id: str, level: int = 1) -> str:
    normalized = (plant_id or "sprout").strip().lower()
    safe_level = min(5, max(1, int(level)))
    candidate_stage = AVATAR_DIR / f"{normalized}_lv{safe_level}.png"
    candidate_base = AVATAR_DIR / f"{normalized}.png"
    fallback_stage = AVATAR_DIR / f"sprout_lv{safe_level}.png"
    fallback_base = AVATAR_DIR / "sprout.png"

    for target in (candidate_stage, candidate_base, fallback_stage, fallback_base):
        if target.exists():
            return target.name

    return ""


def _avatar_slot_config(size_class: str, level: int) -> dict[str, Any]:
    safe_level = min(5, max(1, int(level)))
    by_size = {
        "avatar-lg": {
            1: {"canvas": (680, 510), "display_width": 450, "plant_h_ratio": 0.54, "ground_ratio": 0.85},
            2: {"canvas": (680, 510), "display_width": 450, "plant_h_ratio": 0.58, "ground_ratio": 0.85},
            3: {"canvas": (680, 510), "display_width": 450, "plant_h_ratio": 0.62, "ground_ratio": 0.85},
            4: {"canvas": (680, 510), "display_width": 450, "plant_h_ratio": 0.67, "ground_ratio": 0.85},
            5: {"canvas": (680, 510), "display_width": 450, "plant_h_ratio": 0.72, "ground_ratio": 0.85},
        },
        "avatar-md": {
            1: {"canvas": (740, 520), "display_width": 515, "plant_h_ratio": 0.70, "ground_ratio": 0.90},
            2: {"canvas": (740, 520), "display_width": 515, "plant_h_ratio": 0.74, "ground_ratio": 0.90},
            3: {"canvas": (740, 520), "display_width": 515, "plant_h_ratio": 0.78, "ground_ratio": 0.90},
            4: {"canvas": (740, 520), "display_width": 515, "plant_h_ratio": 0.82, "ground_ratio": 0.90},
            5: {"canvas": (740, 520), "display_width": 515, "plant_h_ratio": 0.86, "ground_ratio": 0.90},
        },
    }
    size_key = size_class if size_class in by_size else "avatar-lg"
    return by_size[size_key][safe_level]


def _avatar_asset_path(plant_id: str, level: int = 1) -> Path | None:
    asset_name = _avatar_asset_name(plant_id, level)
    if not asset_name:
        return None
    target = AVATAR_DIR / asset_name
    if not target.exists():
        return None
    return target


@lru_cache(maxsize=4)
def _available_showcase_plant_ids(level: int = 5) -> tuple[str, ...]:
    ids: set[str] = set()
    suffix = f"_lv{min(5, max(1, int(level)))}.png"
    for path in AVATAR_DIR.glob(f"*{suffix}"):
        name = path.name
        if not name.endswith(suffix):
            continue
        ids.add(name[: -len(suffix)])
    return tuple(sorted(ids))


def _pick_random_showcase_plant_id(level: int = 5) -> str:
    candidates = _available_showcase_plant_ids(level)
    if not candidates:
        return "sprout"
    return random.choice(candidates)


@lru_cache(maxsize=256)
def _render_avatar_canvas_png(plant_id: str, size_class: str, level: int, with_growth_effect: bool) -> bytes:
    target = _avatar_asset_path(plant_id, level)
    if target is None:
        return b""

    spec = _avatar_slot_config(size_class, level)
    canvas_w, canvas_h = spec["canvas"]
    display_level = min(5, max(1, int(level)))

    try:
        from PIL import Image, ImageDraw

        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base)

        # 고정 비율 슬롯 배경을 먼저 깔아 레벨별로 흔들리지 않는 렌더 기준을 만듭니다.
        draw.rounded_rectangle(
            (2, 2, canvas_w - 3, canvas_h - 3),
            radius=max(18, int(canvas_h * 0.08)),
            fill=(255, 255, 255, 40),
            outline=(24, 49, 70, 130),
            width=3,
        )

        plant = Image.open(target).convert("RGBA")
        target_h = max(1, int(canvas_h * float(spec["plant_h_ratio"])))
        target_w = max(1, int(plant.width * (target_h / max(1, plant.height))))
        plant_resized = plant.resize((target_w, target_h), Image.Resampling.NEAREST)

        ground_y = int(canvas_h * float(spec["ground_ratio"]))
        plant_x = (canvas_w - target_w) // 2
        plant_y = ground_y - target_h
        base.alpha_composite(plant_resized, (plant_x, plant_y))

        if with_growth_effect and display_level >= 5:
            fx = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            fx_draw = ImageDraw.Draw(fx)
            points = [
                (0.18, 0.18),
                (0.36, 0.13),
                (0.52, 0.16),
                (0.69, 0.21),
                (0.84, 0.18),
                (0.27, 0.29),
                (0.74, 0.31),
            ]
            for idx, (px, py) in enumerate(points):
                cx = int(canvas_w * px)
                cy = int(canvas_h * py)
                size = 8 if idx % 2 == 0 else 6
                fx_draw.rectangle((cx - size, cy - 1, cx + size, cy + 1), fill=(255, 255, 255, 220))
                fx_draw.rectangle((cx - 1, cy - size, cx + 1, cy + size), fill=(255, 227, 111, 220))
            base = Image.alpha_composite(base, fx)

        out = io.BytesIO()
        base.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return target.read_bytes()



def _render_plant_avatar(
    plant_id: str,
    label: str,
    size_class: str = "avatar-lg",
    level: int = 1,
    with_growth_effect: bool = False,
) -> None:
    safe_level = min(5, max(1, int(level)))
    payload = _render_avatar_canvas_png(plant_id, size_class, safe_level, with_growth_effect)
    if not payload:
        st.markdown("<div class='plant-hero'>🌱</div>", unsafe_allow_html=True)
        return

    display_width = int(_avatar_slot_config(size_class, safe_level)["display_width"])
    st.image(payload, caption=None, width=display_width)


def _concern_label(concern_type: str) -> str:
    labels = {
        "career": "진로 고민",
        "focus": "집중 고민",
        "habit": "습관 고민",
    }
    return labels.get(str(concern_type or "").strip().lower(), "일반 고민")


def _survey_trait_summary(survey_answers: dict[str, Any]) -> str:
    if not isinstance(survey_answers, dict):
        return "설문 데이터 없음"

    cautious = int(survey_answers.get("cautious", 3) or 3)
    support = int(survey_answers.get("needs_support", 3) or 3)
    focus = int(survey_answers.get("focus", 3) or 3)
    small = int(survey_answers.get("small_steps", 3) or 3)

    traits: list[str] = []
    if cautious >= 4:
        traits.append("신중형")
    if support >= 4:
        traits.append("응원형")
    if focus <= 2:
        traits.append("짧은집중형")
    if small >= 4:
        traits.append("작은단계형")

    return ", ".join(traits) if traits else "균형형"


def _to_html_text(text: str) -> str:
    return html.escape(str(text or "")).replace("\n", "<br>")


def _render_chat_card(chat_log_html: str, trigger: int = 0) -> None:
    st.iframe(
        f"""
        <style>
            @font-face {{
                font-family: 'DungGeunMo';
                src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
                font-weight: normal;
                font-style: normal;
                font-display: swap;
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 0 6px 6px 0;
                background: transparent;
                font-family: 'DungGeunMo', 'Press Start 2P', monospace;
                overflow: hidden;
            }}

            .chat-card {{
                padding: 1rem 1rem 0.9rem;
                border: 3px solid #183146;
                background: linear-gradient(180deg, #FDFEFF 0%, #EAF5FF 100%);
                box-shadow: 6px 6px 0 rgba(24, 49, 70, 0.28);
                height: 26rem;
                width: calc(100% - 6px);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}

            .section-note {{
                color: #2C4C63;
                font-family: 'DungGeunMo', 'Press Start 2P', monospace;
                font-size: 0.78rem;
                font-weight: 800;
                line-height: 1.5;
                margin-bottom: 0.2rem;
            }}

            .chat-note {{
                color: #49677B;
                font-family: 'DungGeunMo', 'Press Start 2P', monospace;
                font-size: 0.76rem;
                line-height: 1.45;
                margin-bottom: 0.55rem;
                word-break: keep-all;
            }}

            .chat-log {{
                display: flex;
                flex-direction: column;
                gap: 0.46rem;
                flex: 1 1 auto;
                min-height: 0;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 0.2rem;
            }}

            .chat-log::-webkit-scrollbar {{
                width: 10px;
            }}

            .chat-log::-webkit-scrollbar-thumb {{
                background: #9FB9FF;
                border: 2px solid #183146;
            }}

            .chat-log::-webkit-scrollbar-track {{
                background: rgba(255, 255, 255, 0.5);
            }}

            .chat-bubble {{
                border: 2px solid #183146;
                box-shadow: 2px 2px 0 rgba(24, 49, 70, 0.2);
                padding: 0.5rem 0.58rem;
                font-family: 'DungGeunMo', 'Press Start 2P', monospace;
                font-size: 0.88rem;
                line-height: 1.55;
                max-width: 100%;
                overflow-wrap: anywhere;
                word-break: break-word;
                white-space: pre-wrap;
            }}

            .chat-bubble.bot {{
                align-self: flex-start;
                background: #FFFFFF;
                color: #17334A;
            }}

            .chat-bubble.user {{
                align-self: flex-end;
                background: #FFF4BF;
                color: #1F3B47;
            }}
        </style>
        <div class="chat-card">
            <div class="section-note">식물 친구와 대화</div>
            <div class="chat-note">고민/설문/완료 목표를 기억해서 간단히 코칭해줘요.</div>
            <div id="mindplant-chat-log" class="chat-log">{chat_log_html}</div>
        </div>
        <script>
            const mindPlantScrollTrigger = {trigger};
            const scrollMindPlantChat = () => {{
                const log = document.getElementById('mindplant-chat-log');
                if (log) {{
                    log.scrollTop = log.scrollHeight;
                }}
            }};

            const scheduleMindPlantScroll = () => {{
                requestAnimationFrame(scrollMindPlantChat);
                setTimeout(scrollMindPlantChat, 80);
                setTimeout(scrollMindPlantChat, 240);
                setTimeout(scrollMindPlantChat, 520);
            }};

            scheduleMindPlantScroll();

            const chatLog = document.getElementById('mindplant-chat-log');
            if (chatLog && !chatLog.dataset.scrollObserverAttached) {{
                chatLog.dataset.scrollObserverAttached = 'true';
                const observer = new MutationObserver(scheduleMindPlantScroll);
                observer.observe(chatLog, {{ childList: true, subtree: true }});
            }}
        </script>
        """,
        height=430,
    )


def _persist_state() -> None:
    payload = {
        "page": st.session_state.page,
        "concern_type": st.session_state.concern_type,
        "survey_answers": st.session_state.survey_answers,
        "free_text": st.session_state.free_text,
        "recommendation": st.session_state.recommendation,
        "completed_count": st.session_state.completed_count,
        "today_goal": st.session_state.today_goal,
        "last_encouragement": st.session_state.last_encouragement,
        "goal_history": st.session_state.goal_history,
        "chat_history": st.session_state.chat_history,
    }
    save_user_data(payload, DATA_PATH)


def _default_survey_answers() -> dict[str, int]:
    return {
        "cautious": 3,
        "needs_support": 3,
        "focus": 3,
        "interest_oriented": 3,
        "small_steps": 3,
    }


def _clear_survey_inputs() -> None:
    st.session_state.survey_answers = _default_survey_answers()
    st.session_state.free_text = ""


def _init_state() -> None:
    if st.session_state.get("_initialized"):
        return

    loaded = load_user_data(DATA_PATH)

    st.session_state.page = loaded.get("page", "start")
    st.session_state.concern_type = loaded.get("concern_type", "")
    st.session_state.survey_answers = loaded.get("survey_answers", _default_survey_answers())
    st.session_state.free_text = loaded.get("free_text", "")
    st.session_state.recommendation = loaded.get("recommendation")
    st.session_state.completed_count = int(loaded.get("completed_count", 0) or 0)
    st.session_state.today_goal = loaded.get("today_goal", "")
    st.session_state.last_encouragement = loaded.get("last_encouragement", "")

    loaded_goal_history = loaded.get("goal_history", [])
    st.session_state.goal_history = loaded_goal_history if isinstance(loaded_goal_history, list) else []

    loaded_chat_history = loaded.get("chat_history", [])
    if isinstance(loaded_chat_history, list):
        valid_chat: list[dict[str, str]] = []
        for entry in loaded_chat_history:
            if isinstance(entry, dict):
                role = str(entry.get("role", "assistant"))
                content = str(entry.get("content", "")).strip()
                if content:
                    valid_chat.append({"role": role, "content": content})
        st.session_state.chat_history = valid_chat
    else:
        st.session_state.chat_history = []

    st.session_state.show_particle_burst = False

    st.session_state._initialized = True


_init_state()

theme = _resolve_theme_tokens(int(st.session_state.get("completed_count", 0) or 0))
st.markdown(
    (
        "<style>"
        ":root {"
        f"--theme-bg-top: {theme['bg_top']};"
        f"--theme-bg-mid: {theme['bg_mid']};"
        f"--theme-bg-bottom: {theme['bg_bottom']};"
        f"--theme-accent: {theme['accent']};"
        f"--theme-accent-soft: {theme['accent_soft']};"
        f"--theme-chip: {theme['chip']};"
        "}"
        "</style>"
    ),
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
            @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

            @font-face {
                font-family: 'DungGeunMo';
                src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
                font-weight: normal;
                font-style: normal;
            }

            :root {
                --pixel-ink: #183146;
                --pixel-mint: #9FE8AF;
                --pixel-lime: #62D484;
                --pixel-cream: #FFF6D3;
                --pixel-peach: #FFC58E;
                --pixel-sky: #87D2FF;
                --pixel-shadow: #122538;
                --font-display: 'DungGeunMo', 'Press Start 2P', monospace;
                --font-body: 'DungGeunMo', 'Press Start 2P', monospace;
            }

            .stApp {
                color: var(--pixel-ink);
                font-family: var(--font-body);
                background-color: var(--theme-bg-top);
                background-image:
                    linear-gradient(0deg, rgba(255, 255, 255, 0.18) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.18) 1px, transparent 1px),
                    radial-gradient(circle at 20% 10%, rgba(255, 197, 142, 0.45) 0 11%, transparent 12%),
                    radial-gradient(circle at 78% 12%, rgba(135, 210, 255, 0.42) 0 12%, transparent 13%),
                    linear-gradient(180deg, var(--theme-bg-top) 0%, var(--theme-bg-mid) 48%, var(--theme-bg-bottom) 100%);
                background-size: 18px 18px, 18px 18px, 100% 100%, 100% 100%, 100% 100%;
                background-attachment: fixed;
            }

            .block-container {
                max-width: 1040px;
                padding-top: 1.5rem;
                padding-bottom: 3.2rem;
            }

            h1, h2, h3 {
                font-family: var(--font-display);
                color: var(--pixel-ink);
                letter-spacing: 0.03em;
            }

            h1 {
                font-size: clamp(2.08rem, 6.2vw, 3.24rem);
                line-height: 1.28;
                margin-bottom: 0.48rem;
                text-shadow: 2px 2px 0 #FFFFFF;
            }

            h2 {
                font-size: clamp(1.38rem, 4.2vw, 2.05rem);
                line-height: 1.4;
            }

            h3 {
                font-size: clamp(1.12rem, 3.2vw, 1.55rem);
            }

            p, li, div, span, label, .stCaption {
                color: var(--pixel-ink);
                font-family: var(--font-body);
                font-size: clamp(0.94rem, 1.2vw, 1.05rem);
                letter-spacing: 0.02em;
                line-height: 1.72;
                overflow-wrap: anywhere;
            }

            .stMarkdown,
            .stText,
            .stCaption,
            .stSubheader,
            .stTitle {
                font-family: var(--font-body);
            }

            .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.46rem 0.85rem;
                border: 2px solid var(--pixel-ink);
                background: var(--pixel-cream);
                box-shadow: 3px 3px 0 var(--pixel-shadow);
                font-family: var(--font-display);
                font-size: 0.82rem;
                line-height: 1.5;
                margin-bottom: 1.08rem;
            }

            [data-testid="stImage"] {
                text-align: center;
            }

            [data-testid="stImage"] img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                image-rendering: pixelated;
            }

            .hero-box,
            .panel-card,
            .plant-card,
            .grow-focus {
                padding: 1.38rem 1.42rem;
                border: 3px solid var(--pixel-ink);
                border-radius: 0;
                box-shadow: 6px 6px 0 var(--pixel-shadow);
            }

            .hero-box {
                background:
                    linear-gradient(0deg, rgba(255, 255, 255, 0.22) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.22) 1px, transparent 1px),
                    linear-gradient(160deg, var(--theme-chip) 0%, #FFDFA3 100%);
                background-size: 14px 14px, 14px 14px, 100% 100%;
            }

            .panel-card {
                background: linear-gradient(180deg, #F4FFEE 0%, var(--theme-bg-mid) 100%);
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(180deg, #F4FFEE 0%, var(--theme-bg-mid) 100%);
                border: 3px solid var(--pixel-ink) !important;
                border-radius: 0 !important;
                box-shadow: 6px 6px 0 var(--pixel-shadow);
                padding: 0.9rem 1rem;
            }

            .plant-card {
                background: linear-gradient(180deg, #FFFCE6 0%, var(--theme-bg-bottom) 100%);
            }

            .grow-focus {
                text-align: center;
                margin-bottom: 0.8rem;
                background:
                    linear-gradient(0deg, rgba(255, 255, 255, 0.2) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.2) 1px, transparent 1px),
                    linear-gradient(145deg, var(--theme-bg-mid) 0%, var(--theme-bg-bottom) 100%);
                background-size: 16px 16px, 16px 16px, 100% 100%;
            }

            .chat-card {
                padding: 1rem 1rem 0.9rem;
                border: 3px solid var(--pixel-ink);
                background: linear-gradient(180deg, #FDFEFF 0%, #EAF5FF 100%);
                box-shadow: 6px 6px 0 var(--pixel-shadow);
                height: 26rem;
                min-height: 26rem;
                max-height: 26rem;
                width: 100%;
                box-sizing: border-box;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }

            .chat-log {
                display: flex;
                flex-direction: column;
                gap: 0.46rem;
                flex: 1 1 auto;
                min-height: 0;
                height: auto;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 0.2rem;
                margin-bottom: 0.55rem;
            }

            .chat-log::-webkit-scrollbar {
                width: 10px;
            }

            .chat-log::-webkit-scrollbar-thumb {
                background: #9FB9FF;
                border: 2px solid var(--pixel-ink);
            }

            .chat-log::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.5);
            }

            .chat-bubble {
                border: 2px solid var(--pixel-ink);
                box-shadow: 2px 2px 0 rgba(24, 49, 70, 0.2);
                padding: 0.5rem 0.58rem;
                font-size: 0.88rem;
                line-height: 1.55;
                max-width: 100%;
                overflow-wrap: anywhere;
                word-break: break-word;
                white-space: pre-wrap;
                box-sizing: border-box;
            }

            .chat-bubble.user {
                align-self: flex-end;
                background: #DCEBFF;
            }

            .chat-bubble.bot {
                align-self: flex-start;
                background: #FFFDF4;
            }

            .chat-note {
                font-size: 0.82rem;
                color: #2E4E69;
                margin-bottom: 0.5rem;
                flex: 0 0 auto;
            }

            .avatar-native-note {
                display: none;
            }

            .section-note {
                font-size: 0.98rem;
                margin-bottom: 0.75rem;
                font-weight: 700;
                line-height: 1.6;
            }

            .muted-copy {
                color: #34546C;
                font-size: 0.92rem;
                margin-top: 0.24rem;
                line-height: 1.64;
            }

            .goal-chip {
                display: inline-flex;
                align-items: center;
                padding: 0.38rem 0.68rem;
                margin: 0.2rem 0.28rem 0 0;
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                box-shadow: 2px 2px 0 var(--pixel-shadow);
                background: var(--theme-chip);
                color: var(--pixel-ink);
                font-family: var(--font-display);
                font-size: 0.82rem;
                line-height: 1.5;
                letter-spacing: 0.03em;
                white-space: normal;
                max-width: 100%;
                overflow-wrap: anywhere;
            }

            .goal-row {
                display: flex;
                gap: 0.7rem;
                align-items: flex-start;
                margin-top: 0.55rem;
                padding: 0.66rem 0.74rem;
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                background: #ECFFF4;
                box-shadow: 3px 3px 0 rgba(24, 49, 70, 0.2);
            }

            .goal-index {
                min-width: 1.75rem;
                height: 1.75rem;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border: 2px solid var(--pixel-ink);
                background: var(--pixel-lime);
                color: var(--pixel-ink);
                font-family: var(--font-display);
                font-size: 0.76rem;
                line-height: 1;
                flex: 0 0 auto;
            }

            .goal-text {
                color: var(--pixel-ink);
                line-height: 1.5;
                font-size: 0.96rem;
                font-weight: 700;
                overflow-wrap: anywhere;
            }

            .grow-focus .plant-big {
                font-family: var(--font-display);
                font-size: clamp(1.62rem, 5.8vw, 2.52rem);
                line-height: 1.3;
                margin-top: 0.16rem;
            }

            .grow-focus .soft-text {
                color: #2C4C63;
                font-size: 0.92rem;
                margin-top: 0.3rem;
                font-weight: 700;
                line-height: 1.6;
            }

            .stage-pill {
                display: inline-block;
                margin-top: 0.5rem;
                padding: 0.38rem 0.74rem;
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                background: var(--theme-accent-soft);
                color: var(--pixel-ink);
                font-family: var(--font-display);
                font-size: 0.82rem;
                line-height: 1.5;
                letter-spacing: 0.03em;
                box-shadow: 3px 3px 0 rgba(24, 49, 70, 0.25);
                white-space: normal;
                max-width: 100%;
                overflow-wrap: anywhere;
            }

            .badge-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.42rem;
                margin: 0.35rem 0 0.75rem;
            }

            .stButton > button {
                min-height: 3.55rem;
                border-radius: 0;
                border: 3px solid var(--pixel-ink);
                border-bottom-width: 5px;
                background: linear-gradient(180deg, var(--theme-accent) 0%, var(--theme-accent-soft) 100%);
                color: var(--pixel-ink);
                font-family: var(--font-display);
                font-size: 0.94rem;
                line-height: 1.52;
                letter-spacing: 0.04em;
                text-transform: none;
                box-shadow: 4px 4px 0 var(--pixel-shadow);
                transition: transform 120ms ease, box-shadow 120ms ease;
                padding: 0.5rem 0.62rem;
                white-space: normal;
                overflow-wrap: anywhere;
                word-break: keep-all;
                height: auto;
            }

            .stButton > button:hover {
                transform: translate(-1px, -1px);
                box-shadow: 6px 6px 0 var(--pixel-shadow);
                border-color: var(--pixel-ink);
                color: var(--pixel-ink);
            }

            .stButton > button:active {
                transform: translate(2px, 2px);
                box-shadow: 2px 2px 0 var(--pixel-shadow);
            }

            .stFormSubmitButton > button {
                min-height: 3.3rem;
                border-radius: 0;
                border: 3px solid var(--pixel-ink);
                border-bottom-width: 5px;
                background: linear-gradient(180deg, #EAF5FF 0%, #CFE2FF 100%);
                color: #17334A !important;
                font-family: var(--font-display);
                font-size: 0.92rem;
                line-height: 1.5;
                letter-spacing: 0.03em;
                box-shadow: 4px 4px 0 var(--pixel-shadow);
                transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
            }

            .stFormSubmitButton > button:hover {
                transform: translate(-1px, -1px);
                box-shadow: 6px 6px 0 var(--pixel-shadow);
                background: linear-gradient(180deg, #FFFFFF 0%, #EAF3FF 100%);
                color: #12283A !important;
                border-color: var(--pixel-ink);
            }

            .stFormSubmitButton > button:active {
                transform: translate(2px, 2px);
                box-shadow: 2px 2px 0 var(--pixel-shadow);
            }

            [data-testid="InputInstructions"] {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            .stTextInput input,
            .stTextArea textarea {
                background: #FFFDF4;
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                box-shadow: inset 2px 2px 0 rgba(24, 49, 70, 0.2);
                font-family: var(--font-body);
                font-size: 0.94rem;
                letter-spacing: 0.02em;
                line-height: 1.62;
                color: #111111 !important;
                -webkit-text-fill-color: #111111 !important;
                caret-color: #111111;
            }

            .stTextInput input::placeholder,
            .stTextArea textarea::placeholder {
                color: #4A6276 !important;
                -webkit-text-fill-color: #4A6276 !important;
                opacity: 1;
            }

            .stTextInput label,
            .stTextArea label,
            .stRadio label,
            .stSlider label,
            .stSelectbox label {
                font-family: var(--font-body);
                font-size: 0.92rem;
                letter-spacing: 0.02em;
                line-height: 1.6;
            }

            [data-testid="stRadio"] label,
            [data-testid="stCaptionContainer"],
            .stCaption {
                font-size: 0.9rem;
                line-height: 1.6;
            }

            [data-testid="stMetric"] {
                background: linear-gradient(180deg, #FFFDF4 0%, #ECFFF4 100%);
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                box-shadow: 3px 3px 0 rgba(24, 49, 70, 0.2);
                padding: 0.55rem 0.72rem;
            }

            [data-testid="stMetricLabel"] {
                font-family: var(--font-display);
                font-size: 0.78rem;
                letter-spacing: 0.03em;
                line-height: 1.5;
            }

            [data-testid="stMetricValue"] {
                font-family: var(--font-display);
                font-size: 1.24rem;
                letter-spacing: 0.03em;
                line-height: 1.4;
            }

            [data-testid="stRadio"] {
                padding-top: 0.2rem;
            }

            .stSlider [data-baseweb="slider"] div[role="slider"] {
                border: 2px solid var(--pixel-ink);
                border-radius: 0;
                background: var(--theme-accent-soft);
                box-shadow: 2px 2px 0 rgba(24, 49, 70, 0.25);
            }

            .particle-burst {
                position: relative;
                width: 100%;
                height: 0;
                pointer-events: none;
                z-index: 6;
            }

            .particle-burst span {
                position: absolute;
                left: 50%;
                top: -12px;
                width: 10px;
                height: 10px;
                border: 2px solid var(--pixel-ink);
                background: var(--theme-chip);
                animation: burst-pop 780ms ease-out forwards;
            }

            .particle-burst span:nth-child(2n) {
                background: var(--theme-accent-soft);
            }

            .particle-burst span:nth-child(3n) {
                background: #FFFFFF;
            }

            .particle-burst span:nth-child(1) { --dx: -125px; --dy: -84px; }
            .particle-burst span:nth-child(2) { --dx: -86px; --dy: -102px; }
            .particle-burst span:nth-child(3) { --dx: -46px; --dy: -88px; }
            .particle-burst span:nth-child(4) { --dx: -18px; --dy: -110px; }
            .particle-burst span:nth-child(5) { --dx: 20px; --dy: -105px; }
            .particle-burst span:nth-child(6) { --dx: 56px; --dy: -94px; }
            .particle-burst span:nth-child(7) { --dx: 95px; --dy: -106px; }
            .particle-burst span:nth-child(8) { --dx: 132px; --dy: -86px; }
            .particle-burst span:nth-child(9) { --dx: -112px; --dy: -48px; }
            .particle-burst span:nth-child(10) { --dx: 112px; --dy: -48px; }
            .particle-burst span:nth-child(11) { --dx: -64px; --dy: -66px; }
            .particle-burst span:nth-child(12) { --dx: 64px; --dy: -66px; }

            @keyframes burst-pop {
                0% {
                    opacity: 0;
                    transform: translate(-50%, 0) scale(0.2);
                }
                18% {
                    opacity: 1;
                    transform: translate(-50%, -14px) scale(1);
                }
                100% {
                    opacity: 0;
                    transform: translate(calc(-50% + var(--dx)), var(--dy)) scale(0.35);
                }
            }

            @media (max-width: 640px) {
                .hero-box,
                .plant-card,
                .panel-card,
                .grow-focus {
                    padding: 1.08rem;
                    box-shadow: 4px 4px 0 var(--pixel-shadow);
                }

                h1 {
                    font-size: clamp(1.48rem, 8.1vw, 2rem);
                }

                .stage-pill,
                .goal-chip,
                .stButton > button,
                [data-testid="stMetricLabel"] {
                    font-size: 0.74rem;
                }

                .chat-card {
                    height: 22rem;
                    min-height: 22rem;
                    max-height: 22rem;
                }

                [data-testid="stMetricValue"] {
                    font-size: 1.04rem;
                }
            }
    </style>
    """,
    unsafe_allow_html=True,
)

if not ai_available:
    st.warning("ai.py import에 실패해 임시 fallback 추천 모드로 실행 중입니다.")


if st.session_state.page == "start":
    if not st.session_state.get("start_showcase_plant"):
        st.session_state.start_showcase_plant = _pick_random_showcase_plant_id(level=5)
    st.markdown("<div class='hero-box'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>PRESS START · PIXEL PLANT ADVENTURE</div>", unsafe_allow_html=True)
    _render_plant_avatar(st.session_state.start_showcase_plant, "시작 식물", "avatar-lg", level=5)
    st.title("MindPlant")
    st.subheader("내 마음을 이해하는 AI 식물 친구")
    st.write("작은 퀘스트를 완료하며 식물 친구를 키우는 귀여운 도트 감성 성장 게임")
    st.markdown("<div class='badge-row'><span class='goal-chip'>TINY QUEST LOOP</span><span class='goal-chip'>CUTE PIXEL HUD</span><span class='goal-chip'>GROWTH REWARD</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("시작하기", use_container_width=True):
        st.session_state.page = "concern"
        _persist_state()
        st.rerun()


elif st.session_state.page == "concern":
    st.title("고민 선택")
    st.caption("첫 스테이지: 지금 마음에 가장 가까운 고민을 선택하세요")
    with st.container(border=True):
        st.markdown("<div class='section-note'>지금의 마음에 가장 가까운 주제를 골라주세요.</div>", unsafe_allow_html=True)
        st.markdown("<div class='badge-row'><span class='goal-chip'>진로가 막막해요</span><span class='goal-chip'>집중이 잘 안 돼요</span><span class='goal-chip'>목표를 꾸준히 못 해요</span></div>", unsafe_allow_html=True)
        selected_label = st.radio(
            "지금 가장 가까운 고민을 골라주세요.",
            options=list(CONCERN_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed",
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전", use_container_width=True):
            st.session_state.page = "start"
            _persist_state()
            st.rerun()
    with col2:
        if st.button("다음", use_container_width=True):
            st.session_state.concern_type = CONCERN_OPTIONS[selected_label]
            st.session_state.page = "survey"
            _persist_state()
            st.rerun()


elif st.session_state.page == "survey":
    st.title("성향 설문")
    st.caption("스탯 체크: 1은 낮음, 5는 높음. 지금 느낌대로 선택해요")
    with st.container(border=True):
        st.markdown("<div class='section-note'>정답은 없어요. 지금의 나를 가볍게 체크해보세요.</div>", unsafe_allow_html=True)

        prev = st.session_state.survey_answers or {}

        cautious = st.slider("나는 결정을 내릴 때 신중한 편이다", 1, 5, int(prev.get("cautious", 3)))
        needs_support = st.slider("응원이나 피드백이 있으면 더 잘 실천한다", 1, 5, int(prev.get("needs_support", 3)))
        focus = st.slider("집중을 오래 유지하는 편이다", 1, 5, int(prev.get("focus", 3)))
        interest_oriented = st.slider("흥미가 생기면 몰입이 빨라진다", 1, 5, int(prev.get("interest_oriented", 3)))
        small_steps = st.slider("작은 단계로 나누면 시작이 쉬워진다", 1, 5, int(prev.get("small_steps", 3)))

        st.markdown("<div class='section-note'>지금 고민을 한두 문장으로 적어주세요.</div>", unsafe_allow_html=True)
        free_text = st.text_input(
            "지금 고민을 한두 문장으로 적어주세요",
            value=st.session_state.free_text,
            placeholder="예: 진로를 어떻게 정해야 할지 모르겠어요",
            label_visibility="collapsed",
        )

    if st.button("분석하기", use_container_width=True):
        user_profile = {
            "concern_type": st.session_state.concern_type or "habit",
            "survey_answers": {
                "cautious": cautious,
                "needs_support": needs_support,
                "focus": focus,
                "interest_oriented": interest_oriented,
                "small_steps": small_steps,
            },
            "free_text": free_text,
        }

        recommendation = recommend_plant_fn(user_profile, plants_path=PLANTS_PATH)

        st.session_state.survey_answers = user_profile["survey_answers"]
        st.session_state.free_text = free_text
        st.session_state.recommendation = recommendation
        st.session_state.page = "recommendation"
        _persist_state()
        st.rerun()

    if st.button("고민 다시 선택", use_container_width=True):
        _clear_survey_inputs()
        st.session_state.page = "concern"
        _persist_state()
        st.rerun()


elif st.session_state.page == "recommendation":
    recommendation = st.session_state.recommendation
    if not isinstance(recommendation, dict):
        st.error("추천 결과를 불러오지 못했어요. 다시 시도해 주세요.")
        if st.button("설문으로 돌아가기"):
            st.session_state.page = "survey"
            _persist_state()
            st.rerun()
    else:
        st.title("식물 추천 결과")
        st.markdown("<div class='plant-card'>", unsafe_allow_html=True)
        _render_plant_avatar(
            str(recommendation.get("plant_id", "sprout")),
            "추천 식물",
            "avatar-lg",
            level=5,
        )
        st.markdown("<span class='stage-pill'>나의 식물 친구</span>", unsafe_allow_html=True)
        st.subheader(f"{recommendation.get('plant_name', '식물 친구')}")
        st.write(f"{recommendation.get('personality_summary', '')}")
        st.markdown(f"<div class='muted-copy'>고민 요약 · {recommendation.get('concern_summary', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted-copy'>상징 · {recommendation.get('plant_symbol', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted-copy'>추천 이유 · {recommendation.get('plant_reason', '')}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-note'>시작 목표 예시</div>", unsafe_allow_html=True)
        for idx, goal in enumerate(recommendation.get("starter_goals", []), start=1):
            st.markdown(
                f"<div class='goal-row'><span class='goal-index'>{idx}</span><span class='goal-text'>{goal}</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("이 식물과 시작하기", use_container_width=True):
            st.session_state.last_encouragement = recommendation.get("message", "오늘의 작은 시작을 응원해요.")
            st.session_state.page = "home"
            _persist_state()
            st.rerun()

        if st.button("설문 다시 하기", use_container_width=True):
            _clear_survey_inputs()
            st.session_state.page = "concern"
            _persist_state()
            st.rerun()


elif st.session_state.page == "home":
    recommendation = st.session_state.recommendation or _fallback_recommend_plant({"concern_type": "habit"})
    completed_count = int(st.session_state.completed_count)
    plant_state = build_plant_state(recommendation, completed_count)
    growth_stage = plant_state["growth_stage"]
    current_level = int(growth_stage["level"])

    st.title("MindPlant 홈")
    st.caption("오늘의 목표를 달성할 때마다 경험치가 쌓이고 식물이 성장해요")

    if st.session_state.get("show_particle_burst", False):
        st.markdown(
            "<div class='particle-burst'><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>",
            unsafe_allow_html=True,
        )
        st.session_state.show_particle_burst = False

    if not st.session_state.chat_history:
        opening = (
            f"안녕, 나는 {plant_state['plant_name']}이야. "
            f"너의 {_concern_label(st.session_state.concern_type)} 흐름을 기억하고 있어. "
            "목표 추천이 필요하면 '오늘 목표 추천해줘'라고 말해줘."
        )
        st.session_state.chat_history = [{"role": "assistant", "content": opening}]
        _persist_state()

    left_col, right_col = st.columns([1.28, 0.92], gap="medium")
    with left_col:
        st.markdown("<div class='grow-focus'>", unsafe_allow_html=True)
        _render_plant_avatar(
            plant_state["plant_id"],
            "현재 식물",
            "avatar-md",
            level=current_level,
            with_growth_effect=True,
        )
        st.markdown(f"<div class='plant-big'>{plant_state['plant_name']}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='stage-pill'>STAGE {growth_stage['stage']} · Lv.{growth_stage['level']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='soft-text'>{growth_stage['message']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        chat_items: list[str] = []
        for msg in st.session_state.chat_history[-8:]:
            role = "user" if str(msg.get("role")) == "user" else "bot"
            content_html = _to_html_text(str(msg.get("content", "")))
            chat_items.append(f"<div class='chat-bubble {role}'>{content_html}</div>")

        chat_log_html = "".join(chat_items) if chat_items else "<div class='chat-bubble bot'>아직 대화가 없어요.</div>"
        _render_chat_card(chat_log_html, len(st.session_state.chat_history))

        with st.form("home_chat_form", clear_on_submit=True):
            chat_input = st.text_input(
                "식물 친구에게 할 말",
                placeholder="예: 오늘 목표 추천해줘",
                label_visibility="collapsed",
            )
            send = st.form_submit_button("보내기", use_container_width=True)

        if send and chat_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": chat_input.strip()})
            reply = generate_companion_reply_fn(
                chat_input,
                recommendation,
                st.session_state.concern_type,
                st.session_state.survey_answers,
                completed_count,
                st.session_state.goal_history,
                st.session_state.chat_history,
            )
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.session_state.chat_history = st.session_state.chat_history[-30:]
            _persist_state()
            st.rerun()

    if growth_stage["next_target"] is not None:
        left = int(growth_stage["next_target"]) - completed_count
        st.caption(f"다음 단계까지 {max(0, left)}회 남았어요")
    else:
        st.caption("최고 단계에 도달했어요. 지금의 흐름을 이어가 봐요")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("완료 횟수", f"{completed_count}회")
    with col2:
        st.metric("현재 단계", growth_stage["stage"])

    st.markdown("<div class='badge-row'><span class='goal-chip'>식물 성장 보상</span><span class='goal-chip'>짧은 실천 루프</span><span class='goal-chip'>데모용 핵심 화면</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-note'>오늘의 목표</div>", unsafe_allow_html=True)
    today_goal = st.text_input(
        "오늘의 목표",
        value=st.session_state.today_goal,
        placeholder="예: 수학 문제 5개 풀기",
        label_visibility="collapsed",
    )

    col3, col4 = st.columns(2)
    with col3:
        if st.button("목표 완료", use_container_width=True):
            new_count = completed_count + 1
            next_state = build_plant_state(recommendation, new_count)
            message = generate_encouragement_fn(today_goal.strip(), next_state)

            stripped_goal = today_goal.strip()
            if stripped_goal:
                st.session_state.goal_history.append(stripped_goal)
                st.session_state.goal_history = st.session_state.goal_history[-20:]

            st.session_state.completed_count = new_count
            st.session_state.today_goal = ""
            st.session_state.last_encouragement = message
            st.session_state.show_particle_burst = True
            _persist_state()
            st.rerun()
    with col4:
        if st.button("새 식물로 다시 시작", use_container_width=True):
            # 새 식물 여정을 시작: 추천, 설문, 성장/목표/대화 상태를 초기화
            st.session_state.concern_type = ""
            _clear_survey_inputs()
            st.session_state.recommendation = None
            st.session_state.completed_count = 0
            st.session_state.today_goal = ""
            st.session_state.last_encouragement = ""
            st.session_state.goal_history = []
            st.session_state.chat_history = []
            st.session_state.show_particle_burst = False
            st.session_state.page = "concern"
            _persist_state()
            st.rerun()

    if st.session_state.last_encouragement:
        st.success(st.session_state.last_encouragement)

    if st.button("전체 초기화", use_container_width=True):
        reset_user_data(DATA_PATH)

        st.session_state.page = "start"
        st.session_state.concern_type = ""
        _clear_survey_inputs()
        st.session_state.recommendation = None
        st.session_state.completed_count = 0
        st.session_state.today_goal = ""
        st.session_state.last_encouragement = ""
        st.session_state.goal_history = []
        st.session_state.chat_history = []
        st.session_state.show_particle_burst = False

        _persist_state()
        st.rerun()


else:
    st.session_state.page = "start"
    _persist_state()
    st.rerun()
