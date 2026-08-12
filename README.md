# 📌 MindPlant

> 청소년의 진로, 집중, 습관 고민에 맞는 AI 식물 친구를 추천하고, 작은 목표 실천을 통해 함께 성장하는 Streamlit 기반 MVP입니다.

<br>

## Service

https://mind-plant.streamlit.app/

<br>

## Overview

청소년들은 진로, 집중력, 목표 실천 습관 등 다양한 고민을 안고 있지만, 무겁고 딱딱한 상담 도구는 접근 장벽이 높습니다. MindPlant는 이런 고민을 게임처럼 가볍게 접근할 수 있도록, 사용자의 고민 유형과 성향 설문을 바탕으로 AI가 어울리는 식물 친구를 추천하고, 작은 목표를 꾸준히 실천할 때마다 식물이 성장하는 보상 구조를 통해 지속적인 동기를 부여하는 것을 목표로 기획되었습니다.

<br>

## Approach

* 사용한 데이터
  * `data/plants.json`: 식물별 키워드, 성향 적합도, 추천 목표 등 메타데이터
  * `data/demo_user.json`: 데모 시연용 사용자 상태 데이터
* 주요 로직
  * 고민 유형(진로/집중력/목표 실천) 선택과 5문항 성향 설문(신중함, 응원 필요도, 집중력, 흥미 몰입, 작은 단계 선호) 결과를 조합해 식물 친구를 매칭
  * 목표 완료 횟수를 누적해 5단계(씨앗 → 새싹 → 어린잎 → 줄기 → 꽃) 성장 상태를 계산
* 사용한 모델 또는 기술
  * OpenAI API(GPT 계열 모델)를 통한 식물 친구 추천 사유 생성 및 챗봇 응답 생성
  * API 호출 실패 시를 대비한 규칙 기반 Fallback 추천/응원 로직
  * SQLite 기반 사용자 상태 저장(`src/db.py`)과 Streamlit `session_state`를 통한 화면 간 상태 공유
* 전체적인 접근 방식
  * 고민 선택 → 성향 설문 → AI 식물 친구 추천 → 오늘의 목표 실천 → 식물 성장 → 식물 친구와의 대화로 이어지는 단계별 사용자 흐름 설계

<br>

## Results

* 고민 유형과 성향 설문을 조합한 AI 식물 친구 추천 및 API 실패 시 자연스러운 Fallback 응답 제공
* 목표 완료 횟수에 따른 5단계 식물 성장(씨앗~꽃)과 단계별 아바타 이미지, 배경 테마 자동 전환 구현
* 추천 성향, 최근 완료 목표를 반영한 식물 친구와의 실시간 대화 기능 구현
* 상태 공유 이슈를 `st.session_state` 단일 소스로 관리해 화면 전환 간 데이터 불일치 문제 해결

<!-- 필요한 경우 그래프나 결과 이미지를 추가합니다. -->

<br>

## Tech Stack

### Languages

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

### Web Framework

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

### AI & LLM

![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)

### Database

![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

### Image Processing

![Pillow](https://img.shields.io/badge/Pillow-3776AB?style=flat-square&logo=python&logoColor=white)

### Development & Environment

![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)
![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=flat-square&logo=visualstudiocode&logoColor=white)

<br>

## Getting Started

필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

애플리케이션을 실행합니다.

```bash
streamlit run src/app.py
```

프로젝트 루트에 `.env` 파일을 생성한 후 아래 내용을 입력합니다.

```env

# APIM Foundry Proxy Base URL
APIM_BASE_URL=https://apim-foundryproxy-dev.azure-api.net/foundry

# APIM에서 발급받은 API Key
APIM_KEY=your_apim_key

# Model Configuration
CHAT_MODEL=gpt-5.4
EMBEDDING_MODEL=text-embedding-3-small
VISION_MODEL=gpt-5.4
```

### 환경 변수 설명

| 변수                | 설명                                           |
| ----------------- | -------------------------------------------- |
| `APIM_BASE_URL`   | APIM Foundry Proxy의 기본 URL (`/foundry`까지 입력) |
| `APIM_KEY`        | APIM에서 발급받은 공통 API Key                       |
| `CHAT_MODEL`      | 대화 생성에 사용하는 모델                               |
| `EMBEDDING_MODEL` | 임베딩 생성에 사용하는 모델                              |
| `VISION_MODEL`    | 이미지 이해에 사용하는 모델                              |

<br>

## Project Structure

```text
mindplant/
├── assets/
│   └── plants/
│       ├── basil.png
│       ├── cactus.png
│       ├── lavender.png
│       ├── mint.png
│       ├── monstera.png
│       ├── sprout.png
│       ├── sunflower.png
│       ├── basil_lv1.png ~ basil_lv5.png
│       ├── cactus_lv1.png ~ cactus_lv5.png
│       ├── lavender_lv1.png ~ lavender_lv5.png
│       ├── mint_lv1.png ~ mint_lv5.png
│       ├── monstera_lv1.png ~ monstera_lv5.png
│       ├── sprout_lv1.png ~ sprout_lv5.png
│       └── sunflower_lv1.png ~ sunflower_lv5.png
├── data/
│   ├── demo_user.json
│   └── plants.json
├── src/
│   ├── ai.py
│   ├── app.py
│   ├── db.py
│   ├── growth.py
│   ├── storage.py
│   └── test_growth.py
├── design.md
├── README.md
├── requirements.txt
└── run_app.ps1
```

### 주요 파일

| 파일                    | 설명                          |
| --------------------- | --------------------------- |
| `src/app.py`          | Streamlit UI 및 전체 애플리케이션 흐름 |
| `src/ai.py`           | AI 추천, 챗봇 응답 생성 및 LLM 호출    |
| `src/db.py`           | SQLite 기반 사용자 상태 저장/조회      |
| `src/growth.py`       | 식물 성장 단계 계산                 |
| `src/storage.py`      | 사용자 데이터 저장 및 불러오기 유틸리티(세션 간 상태 공유 문제를 막기 위해 현재 `app.py`에서는 사용하지 않으며, 상태는 `st.session_state`에만 보관됩니다) |
| `src/test_growth.py`  | 성장 단계 계산 로직 단위 테스트          |
| `data/plants.json`    | 식물 메타데이터 및 추천 기준            |
| `data/demo_user.json` | 데모 사용자 데이터                  |
| `assets/plants/`      | 식물 및 성장 단계 이미지              |
| `design.md`           | 디자인 시스템 및 UI 가이드            |

<br>

## Notes

* API 호출 실패 상황을 고려한 Fallback 로직 덕분에 외부 API 장애 시에도 데모 흐름이 끊기지 않도록 안정성을 확보했습니다.
* 사용자 상태를 여러 저장 방식(`storage.py`, `db.py`, `session_state`)으로 실험하는 과정에서 세션 간 상태 공유 문제를 겪었고, 현재는 `st.session_state`를 단일 소스로 사용해 문제를 해결했습니다.
* 향후 SQLite 저장소를 정식으로 연동해 여러 사용자의 진행 상태를 영구적으로 관리하는 기능을 확장할 예정입니다.

<br>

## License

Copyright © 2026 Youth-AI Project Team 5. All rights reserved.

This repository is provided for viewing and portfolio evaluation purposes only.

No permission is granted to copy, modify, distribute, sublicense, publish, or commercially use any part of this project, including its source code, assets, documentation, design, or other contents, without prior written permission from the copyright holder.

If you want to use this project or any portion of it, please obtain written permission from the repository owner in advance.
