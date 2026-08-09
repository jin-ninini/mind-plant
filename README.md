# MindPlant

청소년의 진로, 집중, 습관 고민에 맞는 AI 식물 친구를 추천하고, 작은 목표 실천을 통해 함께 성장하는 Streamlit 기반 MVP입니다.

## 서비스

https://mind-plant.streamlit.app/

## 1. 프로젝트 소개

MindPlant는 사용자가 고민 유형과 성향 설문을 입력하면 AI가 어울리는 식물 친구를 추천하는 서비스입니다. 사용자는 오늘의 작은 목표를 설정하고 완료할 수 있으며, 목표를 꾸준히 실천할수록 식물 친구가 성장합니다.

홈 화면에서는 추천받은 식물 친구와 대화할 수 있습니다. 챗봇은 사용자의 고민 유형, 성향 설문 결과, 추천 목표, 최근 완료한 목표를 바탕으로 다음 행동을 제안하거나 응원의 메시지를 제공합니다.

## 2. 주요 기능

* 고민 유형 선택

  * 진로 고민
  * 집중력 고민
  * 목표 실천 고민
* 성향 설문

  * 신중함
  * 응원 필요도
  * 집중력
  * 흥미 몰입
  * 작은 단계 선호
* GPT 기반 AI 식물 친구 추천
* API 호출 실패 시 Fallback 추천 및 응원 로직 제공
* 오늘의 목표 생성 및 완료 기록
* 완료 횟수에 따른 식물 성장

  * 씨앗
  * 새싹
  * 어린잎
  * 줄기
  * 꽃
* 식물별 성장 단계 아바타 제공
* 식물 친구와의 대화 기능
* 채팅창 자동 스크롤
* 서버 종료 안내 메시지 출력

## 3. 실행 방법

필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

애플리케이션을 실행합니다.

```bash
streamlit run src/app.py
```

## 4. 환경 변수

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


## 5. 프로젝트 구조

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
| `src/growth.py`       | 식물 성장 단계 계산                 |
| `src/storage.py`      | 사용자 데이터 저장 및 불러오기           |
| `data/plants.json`    | 식물 메타데이터 및 추천 기준            |
| `data/demo_user.json` | 데모 사용자 데이터                  |
| `assets/plants/`      | 식물 및 성장 단계 이미지              |
| `design.md`           | 디자인 시스템 및 UI 가이드            |

## 6. License

Copyright © 2026 Hyunjin.Hwang (@jin-ninini) All rights reserved.

This repository is provided for viewing and portfolio evaluation purposes only.

No permission is granted to copy, modify, distribute, sublicense, publish, or commercially use any part of this project, including its source code, assets, documentation, design, or other contents, without prior written permission from the copyright holder.

If you wish to use this project or any portion of it, please obtain written permission from the repository owner in advance.
