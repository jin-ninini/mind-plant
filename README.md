# 🌱 Mind-Plant

> 청소년의 진로, 집중, 습관 고민에 맞는 식물 친구를 추천하고 작은 목표 실천으로 함께 성장하는 Streamlit 기반 MVP

**Service**: https://mind-plant.streamlit.app/

<br>

## Overview

청소년은 진로, 집중력, 목표 실천 습관 등 다양한 고민을 안고 있지만 무겁고 딱딱한 상담 도구는 접근 장벽이 높습니다. MindPlant는 고민 유형과 성향 설문을 바탕으로 AI가 어울리는 식물 친구를 추천하고, 작은 목표를 실천할 때마다 식물이 자라는 보상 구조로 꾸준한 동기를 부여합니다. 그 결과 고민 선택부터 목표 실천, 식물 친구와의 대화까지 이어지는 게임형 자기관리 흐름을 구현했습니다.

<br>

## Approach

- **Data**: `data/plants.json`에 식물 32종의 키워드, 고민 유형, 성향 적합도, 추천 목표를 정의하고 `data/demo_user.json`으로 데모 상태 제공
- **User Flow**: 로그인 → MBTI 4문항 → 고민 유형 선택(진로/집중/습관/기타) → 5문항 성향 설문 → 식물 추천 → 목표 실천 및 물주기 → 홈 화면 대화
- **Matching**: 고민 유형과 성향 설문(신중함, 응원 필요도, 집중력, 흥미 몰입, 작은 단계 선호) 결과를 조합해 식물 친구 매칭
- **LLM**: OpenAI 호환 API(APIM Foundry Proxy 지원)로 추천 사유, 응원 메시지, 목표 제안 및 세분화 생성
- **Agent**: 홈 화면 식물 친구가 Tool Calling 루프(최대 4단계)로 진행 상황 조회, 완료 기록 조회, 오늘의 목표 설정 및 선택, 장기 기억 저장 도구를 스스로 골라 실행
- **Memory**: 최근 대화 8개를 단기 기억으로, 에이전트가 저장한 사용자 정보(최대 10개)를 장기 기억으로 프롬프트에 주입
- **Fallback**: API 키가 없거나 호출이 실패하면 규칙 기반 추천과 응답으로 자동 전환
- **Growth**: 목표 완료 횟수를 누적해 5단계 성장 상태와 경험치(완료 1회당 500 EXP) 계산
- **Storage**: SQLite(`data/mindplant.db`)에 사용자별 상태를 저장하고 `st.session_state`로 화면 간 상태 공유

<br>

## Results

| Stage | Level | Completed Goals | Message |
|---|---|---|---|
| 🌱 씨앗 | 1 | 0 | 아직 작은 가능성이 잠들어 있어요 |
| 🌿 새싹 | 2 | 1–2 | 첫 실천으로 싹이 텄어요 |
| 🪴 어린잎 | 3 | 3–5 | 꾸준함이 보이기 시작했어요 |
| 🌳 줄기 | 4 | 6–9 | 스스로를 믿는 힘이 자라고 있어요 |
| 🌻 꽃 | 5 | 10+ | 작은 목표들이 멋진 변화가 되었어요 |

- AI가 고민 유형과 성향 설문을 조합해 식물 친구를 추천하고, API 실패 시에도 Fallback으로 자연스럽게 응답
- 성장 단계에 따라 식물 32종의 단계별 아바타 이미지와 배경 테마가 자동으로 전환
- 식물 친구가 대화 중 필요한 도구를 직접 호출해 오늘의 목표를 채우고 사용자 정보를 기억
- 홈 화면에서 에이전트가 실행한 도구 내역과 저장된 기억을 확인 가능

<br>

## Tech Stack

| Category | Stack |
|---|---|
| Languages | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square\&logo=python\&logoColor=white) |
| Web Framework | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square\&logo=streamlit\&logoColor=white) |
| NLP & LLM | ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square\&logo=openai\&logoColor=white) |
| Database | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square\&logo=sqlite\&logoColor=white) |
| Big Data & Cloud | ![Microsoft Azure](https://img.shields.io/badge/Microsoft%20Azure-0078D4?style=flat-square\&logoColor=white) |
| Development & Environment | ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square\&logo=git\&logoColor=white)  ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square\&logo=github\&logoColor=white)  ![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=flat-square\&logoColor=white) |

<br>

## Project Structure

```text
mind-plant/
├── .devcontainer/           # GitHub Codespaces 개발 환경 설정
├── assets/
│   └── plants/              # 식물 32종 기본 이미지 + 성장 단계별 이미지 ({plant_id}_lv1~lv5.png)
├── data/
│   ├── demo_user.json       # 데모 사용자 상태
│   ├── mindplant.db         # SQLite 사용자 상태 DB
│   └── plants.json          # 식물 메타데이터와 추천 기준
├── src/
│   ├── app.py               # Streamlit UI와 전체 화면 흐름
│   ├── agent.py             # 식물 친구 에이전트(도구 정의, Tool Calling 루프, 장기 기억)
│   ├── ai.py                # 식물 추천, 응원, 목표 제안, 챗봇 응답 생성(LLM 호출)
│   ├── db.py                # SQLite 사용자 상태 저장/조회
│   ├── growth.py            # 성장 단계와 경험치 계산
│   ├── storage.py           # JSON 파일 저장 유틸리티(현재 app.py에서 미사용)
│   ├── test_agent.py        # 에이전트 루프와 도구 단위 테스트(가짜 LLM 사용)
│   └── test_growth.py       # 성장 로직 단위 테스트
├── .env.example             # 환경 변수 예시
├── design.md                # 디자인 시스템과 UI 가이드
├── MindPlant_presentation_final.pdf
├── MindPlant_presentation_v1.pdf
├── requirements.txt
├── run_app.ps1              # Windows용 실행 스크립트
└── README.md
```

<br>

## Getting Started

```bash
pip install -r requirements.txt
cp .env.example .env         # APIM_KEY 등 값 입력
streamlit run src/app.py
```

Windows PowerShell에서는 `./run_app.ps1`로 실행할 수 있습니다.

단위 테스트를 실행합니다.

```bash
cd src
python -m unittest test_agent test_growth
```

| Variable | Description |
|---|---|
| `APIM_BASE_URL` | APIM Foundry Proxy 기본 URL(`/foundry`까지 입력) |
| `APIM_KEY` | APIM에서 발급받은 공통 API Key |
| `CHAT_MODEL` | 추천과 대화 생성에 사용하는 모델 |
| `EMBEDDING_MODEL` | 임베딩 생성에 사용하는 모델 |
| `VISION_MODEL` | 이미지 이해에 사용하는 모델 |

- `APIM_BASE_URL` 대신 `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`로 OpenAI 호환 API에 직접 연결 가능
- API 키가 없어도 규칙 기반 Fallback으로 전체 흐름 체험 가능

<br>

## Notes

- Fallback 로직을 먼저 설계해 API 장애나 키 미설정 상황에서도 시연이 끊기지 않도록 구성
- 세션 간 상태가 섞이는 문제를 막기 위해 `storage.py` 대신 SQLite와 `st.session_state` 조합으로 전환
- 키워드 규칙으로 처리하던 목표 추가를 LLM의 도구 선택으로 바꿔 자연어 요청 대응 범위 확대
- 에이전트가 실패하면 기존 규칙 기반 흐름으로 넘어가도록 설계해 안정성 유지

<br>

## License

Copyright © 2026 Youth-AI Project Team 5. All rights reserved.

This repository is provided for viewing and portfolio evaluation purposes only.

No permission is granted to copy, modify, distribute, sublicense, publish, or commercially use any part of this project, including its source code, assets, documentation, design, or other contents, without prior written permission from the copyright holder.

If you want to use this project or any portion of it, please obtain written permission from the repository owner in advance.
