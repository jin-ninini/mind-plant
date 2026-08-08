"""
config.py
=========
APIM(Foundry Proxy)에 연결하는 OpenAI 호환 클라이언트를 만드는 곳입니다.

유지보수 포인트를 이 파일 하나로 모아뒀습니다.
- API 키/베이스 URL/모델명이 바뀌면 프로젝트 루트의 .env 파일만 수정하면 됩니다.
- ai.py를 포함한 다른 코드에서는 키를 직접 다루지 말고, 항상 이 파일의 함수를 통해 client를 받아 쓰세요.

Foundry Proxy 구조:
    {APIM_BASE_URL}/{MODEL_NAME}/   ← 모델마다 URL 경로가 다릅니다.
    인증은 헤더 "api-key: {APIM_KEY}" 로 합니다. (모든 모델 공통 키)

APIM_KEY가 없어도 앱은 죽지 않습니다. is_configured()가 False를 반환하고,
ai.py는 그 경우 규칙 기반 fallback 로직으로 자동 전환됩니다.
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

# 프로젝트 어디서 실행하든 .env 를 자동으로 찾아서 로드합니다.
load_dotenv(find_dotenv(usecwd=True), override=True)


def _clean(value: str | None, default: str = "") -> str:
    """따옴표가 섞여 들어와도('...' 또는 "...") 깔끔하게 정리합니다."""
    return (value if value is not None else default).strip().strip('"').strip("'")


# ------------------------------------------------------------------
# .env 에서 읽어오는 값들 (이름만 맞으면 .env 값만 바꿔도 전체 반영됨)
# ------------------------------------------------------------------
APIM_BASE_URL = _clean(os.getenv("APIM_BASE_URL")).rstrip("/")
APIM_KEY = _clean(os.getenv("APIM_KEY"))

CHAT_MODEL = _clean(os.getenv("CHAT_MODEL"), "gpt-5.4")
EMBEDDING_MODEL = _clean(os.getenv("EMBEDDING_MODEL"), "text-embedding-3-small")
VISION_MODEL = _clean(os.getenv("VISION_MODEL"), "gpt-5.4")


def is_configured() -> bool:
    """APIM 호출에 필요한 값이 모두 채워졌는지 확인합니다."""
    return bool(APIM_BASE_URL and APIM_KEY)


def get_client(model_name: str) -> OpenAI:
    """
    주어진 모델용 OpenAI 호환 클라이언트를 반환합니다.
    Foundry Proxy는 모델마다 base_url 경로가 다르므로, 모델명을 넣어서 client를 만듭니다.

    사용 예:
        client = get_client(CHAT_MODEL)
        client.chat.completions.create(model=CHAT_MODEL, messages=[...])
    """
    if not is_configured():
        raise RuntimeError(
            "[config.py] APIM_BASE_URL / APIM_KEY 가 설정되지 않았습니다. "
            "프로젝트 루트의 .env 파일을 확인하세요. (.env.example 참고)"
        )
    return OpenAI(
        api_key="placeholder",  # APIM은 api-key 헤더로 인증하므로 여기는 아무 값이나 OK
        base_url=f"{APIM_BASE_URL}/{model_name}/",
        default_headers={"api-key": APIM_KEY},
        timeout=20.0,
    )


def get_chat_client() -> OpenAI:
    """채팅(텍스트 생성)용 클라이언트."""
    return get_client(CHAT_MODEL)


def get_embedding_client() -> OpenAI:
    """임베딩용 클라이언트."""
    return get_client(EMBEDDING_MODEL)


def get_vision_client() -> OpenAI:
    """이미지 인식(비전)용 클라이언트."""
    return get_client(VISION_MODEL)


if __name__ == "__main__":
    # 환경변수가 잘 로드되는지 빠르게 확인하는 용도: python -m src.config (프로젝트 루트에서)
    print("APIM_BASE_URL:", APIM_BASE_URL or "(비어있음)")
    print("CHAT_MODEL:", CHAT_MODEL)
    print("EMBEDDING_MODEL:", EMBEDDING_MODEL)
    print("VISION_MODEL:", VISION_MODEL)
    print("is_configured():", is_configured())
    if APIM_KEY:
        print("APIM_KEY:", APIM_KEY[:4] + "..." + APIM_KEY[-4:])
