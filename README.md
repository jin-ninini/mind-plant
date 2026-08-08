# MindPlant

청소년의 진로, 집중, 습관 고민에 맞는 AI 식물 친구를 추천하고, 작은 목표 실천으로 함께 성장하는 Streamlit 기반 MVP입니다.

## 1) 프로젝트 소개

MindPlant는 사용자가 고민 유형과 성향 설문을 입력하면 AI가 어울리는 식물 친구를 추천해 주는 서비스입니다. 사용자는 오늘의 작은 목표를 설정하고 완료할 수 있으며, 완료 횟수에 따라 식물 아바타가 성장합니다.

홈 화면에서는 식물 친구와 짧게 대화할 수 있습니다. 챗봇은 고민 유형, 설문 성향, 추천 목표, 최근 완료 목표를 참고해 다음 행동을 제안하거나 응원 메시지를 제공합니다.

AI 호출은 사내 **APIM(Foundry Proxy)** 을 통해 이루어집니다.

## 2) 주요 기능

- 고민 유형 선택: 진로 고민, 집중력 고민, 목표 실천 고민
- 성향 설문: 신중함, 응원 필요도, 집중력, 흥미 몰입, 작은 단계 선호
- APIM(Foundry Proxy) 기반 식물 친구 추천
- API 키가 없거나 호출 실패 시 fallback 추천/응원 로직 사용
- 오늘의 목표 완료 및 완료 이력 저장
- 완료 횟수 기반 성장 단계: 씨앗, 새싹, 어린잎, 줄기, 꽃
- 식물별 성장 단계 아바타 표시
- 식물 친구와 대화하는 챗봇 UI
- 채팅창 자동 하단 스크롤
- 터미널에 서버 종료 안내 출력

## 3) 실행 방법

필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

`.env` 파일을 준비합니다. (자세한 내용은 4번 항목 참고)

```bash
cp .env.example .env
```

일반 실행 (**반드시 프로젝트 루트에서 실행**하세요):

```bash
streamlit run src/app.py
```

Windows PowerShell 권장 실행:

```powershell
.\run_app.ps1
```

`run_app.ps1`로 실행하면 터미널에 서버 종료 안내가 출력되고, `Ctrl+C` 입력 시 Streamlit 프로세스를 정리합니다. `streamlit run src/app.py`로 직접 실행해도 앱 시작 시 터미널에 `Ctrl+C` 종료 안내가 한 번 출력됩니다.

## 4) 환경 변수

로컬 테스트용 `.env` 파일을 **프로젝트 루트**에 만들고 아래 값을 설정합니다. (이미 채워진 `.env`가 있다면 그대로 사용하면 됩니다.)

```env
APIM_BASE_URL=https://apim-foundryproxy-dev.azure-api.net/foundry
APIM_KEY=발급받은_키
CHAT_MODEL=gpt-5.4
EMBEDDING_MODEL=text-embedding-3-small
VISION_MODEL=gpt-5.4
```

변수 설명:

- `APIM_BASE_URL`: Foundry Proxy 베이스 URL (모델명 없이 `/foundry`까지). 실제 요청 시에는 `{APIM_BASE_URL}/{모델명}/` 형태로 모델별 경로가 붙습니다.
- `APIM_KEY`: 운영자가 발급해준 APIM 공통 키입니다. 모든 모델 호출에 `api-key` 헤더로 사용됩니다.
- `CHAT_MODEL` / `EMBEDDING_MODEL` / `VISION_MODEL`: 용도별로 사용할 모델명입니다.

`src/config.py`가 `.env`를 읽어서 클라이언트를 만들고, `src/ai.py`는 그 클라이언트만 가져다 씁니다. **키/URL/모델을 바꿀 때는 `.env`만 수정하면 되고, 코드는 건드릴 필요가 없습니다.**

`APIM_KEY`가 비어 있어도 앱은 죽지 않습니다. `src/config.py`의 `is_configured()`가 `False`를 반환하고, `src/ai.py`는 규칙 기반 fallback 추천/응원 로직으로 자동 전환됩니다.

중요: `.env`는 API 키를 포함하므로 GitHub에 올리지 마세요. (`.gitignore`에 이미 등록되어 있습니다.)

## 5) 파일 구조

```text
mindplant/
  README.md
  requirements.txt
  .env               # 실제 키 (git에 올리지 않음)
  .env.example        # 팀원 공유용 템플릿 (키는 비워둠)
  .gitignore
  plants.json
  run_app.ps1
  design.md
  src/
    __init__.py
    config.py          # APIM 클라이언트 생성 (유지보수 핵심 파일)
    app.py              # Streamlit 화면, 페이지 흐름, 챗봇 UI
    ai.py               # 식물 추천 / 응원 메시지 / 챗봇 답변 생성
    growth.py           # 완료 횟수 기반 성장 단계 계산
    storage.py          # data/demo_user.json 기반 상태 저장/불러오기
  assets/
    plants/
      basil.png
      cactus.png
      lavender.png
      mint.png
      monstera.png
      sprout.png
      sunflower.png
      basil_lv1.png ~ basil_lv5.png
      cactus_lv1.png ~ cactus_lv5.png
      lavender_lv1.png ~ lavender_lv5.png
      mint_lv1.png ~ mint_lv5.png
      monstera_lv1.png ~ monstera_lv5.png
      sprout_lv1.png ~ sprout_lv5.png
      sunflower_lv1.png ~ sunflower_lv5.png
  data/
    demo_user.json
```

파일 역할:

- `src/config.py`: `.env` 값을 읽어 APIM용 OpenAI 호환 클라이언트를 만드는 곳. **API 키/URL 관련 로직은 전부 여기에만 있습니다.**
- `src/app.py`: Streamlit 화면, 페이지 흐름, 목표 완료, 챗봇 UI, 식물 아바타 렌더링
- `src/ai.py`: `config.py`의 클라이언트로 APIM 호출, 식물 추천, 응원 메시지, 챗봇 답변 생성
- `src/growth.py`: 완료 횟수에 따른 성장 단계 계산
- `src/storage.py`: `data/demo_user.json` 기반 사용자 상태 저장/불러오기
- `plants.json`: 식물 메타데이터와 추천 기준 (프로젝트 루트에 위치, 값을 수정/추가해서 커스터마이즈 가능)
- `run_app.ps1`: Windows PowerShell용 실행/종료 보조 스크립트
- `design.md`: 현재 앱의 픽셀 UI, 색상, 타이포그래피, 컴포넌트 규칙을 정리한 디자인 재현 문서
- `assets/plants/*.png`: 식물별 기본 및 성장 단계 도트 아바타 이미지
- `data/demo_user.json`: 데모용 사용자 상태 데이터

## 6) 데이터 저장 방식

현재 MVP는 별도 DB 없이 `data/demo_user.json`에 상태를 저장합니다.

저장되는 주요 값:

- 현재 페이지
- 선택한 고민 유형
- 설문 답변
- 추천 결과
- 완료 횟수
- 오늘의 목표
- 최근 완료 목표 이력
- 챗봇 대화 이력

공유 배포용 데모에서는 여러 사용자가 같은 JSON 상태를 공유할 수 있습니다. 사용자별 장기 기록이 필요하면 Supabase 같은 외부 DB로 확장하는 것이 좋습니다.

**내일 실제 데이터로 교체하려면?**

- 식물 종류/추천 기준을 바꾸고 싶다면 `plants.json`만 수정하면 됩니다. (형식은 기존 항목과 동일하게 `id`, `name`, `emoji`, `keywords`, `concern_types`, `symbol`, `description`, `starter_goals`)
- 새 식물을 추가하면 `assets/plants/`에 `{id}.png`, `{id}_lv1.png` ~ `{id}_lv5.png` 이미지도 함께 넣어주세요. (없으면 sprout 이미지로 자동 대체됩니다.)
- 초기 데모 상태를 리셋하고 싶다면 `data/demo_user.json`을 지우거나, 앱 화면의 "전체 초기화" 버튼을 누르면 됩니다.

## 7) 배포 메모

가장 쉬운 배포 방식은 Streamlit Community Cloud입니다.

1. GitHub repository를 만듭니다.
2. `.env`, `__pycache__/`, `*.pyc`, 로컬 로그 파일은 커밋하지 않습니다.
3. Streamlit Community Cloud에서 repo와 entrypoint `src/app.py`를 선택합니다.
4. Advanced settings의 Secrets에 아래 값을 등록합니다.

```toml
APIM_BASE_URL = "https://apim-foundryproxy-dev.azure-api.net/foundry"
APIM_KEY = "발급받은_키"
CHAT_MODEL = "gpt-5.4"
EMBEDDING_MODEL = "text-embedding-3-small"
VISION_MODEL = "gpt-5.4"
```

권장 `.gitignore`는 이미 프로젝트에 포함되어 있습니다 (`.env`, `__pycache__/`, `*.pyc` 등).

## 8) 3분 발표 데모 시나리오

1. 문제 제시 (30초)
   - 청소년이 진로, 집중, 습관 고민으로 시작이 어렵다는 문제를 소개합니다.
2. 서비스 한 줄 설명 (20초)
   - "고민을 입력하면 나에게 맞는 식물 친구와 작은 실천 목표를 제안하는 서비스"라고 소개합니다.
3. 실시간 추천 시연 (70초)
   - 예시 고민 입력: "요즘 진로가 막막하고 공부 집중이 잘 안 돼요."
   - 추천 식물 결과, 상징, 추천 이유, 시작 목표를 보여줍니다.
4. 성장 경험 시연 (40초)
   - 목표 1개를 완료 처리하고 식물 성장 변화와 응원 메시지를 보여줍니다.
5. 챗봇 시연 (20초)
   - "오늘 목표 추천해줘"라고 입력해 식물 친구가 맥락 기반으로 답하는 모습을 보여줍니다.
6. 마무리 (20초)
   - "작은 행동의 반복이 자기효능감을 키운다"는 핵심 가치를 강조합니다.

## 9) MVP 범위와 확장

현재는 JSON 기반으로 빠르게 검증하는 MVP입니다.

확장 아이디어:

- Supabase 연동으로 사용자별 장기 기록 저장
- 로그인/사용자 프로필
- 랭킹 또는 커뮤니티 기능
- 목표 추천 개인화 강화
- Vercel 기반 랜딩 페이지와 Streamlit 앱 링크 연결

## 10) 유지보수 가이드

- **API 키/모델을 바꿀 때**: `.env` 파일만 수정하세요. 코드 수정 불필요.
- **AI 호출 로직을 건드릴 때**: `src/ai.py`만 보면 됩니다. 클라이언트 생성 로직은 `src/config.py`에 있으니 직접 `OpenAI(...)`를 새로 만들지 마세요.
- **팀원과 공유할 때**: `.env`는 공유하지 말고 `.env.example`만 공유하세요. 각자 `.env`를 직접 만들도록 안내하세요.
- **GitHub에 올릴 때**: 커밋 전에 `git status`로 `.env`가 안 보이는지 한 번 더 확인하는 습관을 들이세요.
