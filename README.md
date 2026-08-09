# MindPlant

청소년의 진로, 집중, 습관 고민에 맞는 AI 식물 친구를 추천하고, 작은 목표 실천으로 함께 성장하는 Streamlit 기반 MVP입니다.

## 1) 프로젝트 소개

MindPlant는 사용자가 고민 유형과 성향 설문을 입력하면 AI가 어울리는 식물 친구를 추천해 주는 서비스입니다. 사용자는 오늘의 작은 목표를 설정하고 완료할 수 있으며, 완료 횟수에 따라 식물 아바타가 성장합니다.

홈 화면에서는 식물 친구와 짧게 대화할 수 있습니다. 챗봇은 고민 유형, 설문 성향, 추천 목표, 최근 완료 목표를 참고해 다음 행동을 제안하거나 응원 메시지를 제공합니다.

## 2) 주요 기능

- 고민 유형 선택: 진로 고민, 집중력 고민, 목표 실천 고민
- 성향 설문: 신중함, 응원 필요도, 집중력, 흥미 몰입, 작은 단계 선호
- Gemini API 기반 식물 친구 추천
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

일반 실행:

```bash
streamlit run src/app.py
```

Windows PowerShell 권장 실행:

```powershell
.\run_app.ps1
```

`run_app.ps1`로 실행하면 터미널에 서버 종료 안내가 출력되고, `Ctrl+C` 입력 시 Streamlit 프로세스를 정리합니다. `streamlit run src/app.py`로 직접 실행해도 앱 시작 시 터미널에 `Ctrl+C` 종료 안내가 한 번 출력됩니다.

## 4) 환경 변수

로컬 테스트용 `.env` 파일을 프로젝트 루트에 만들고 아래 값을 설정합니다.

```env
OPENAI_API_KEY="your_gemini_api_key"
OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_MODEL="gemini-3.1-flash-lite"
```

변수 설명:

- `OPENAI_API_KEY`: Gemini API 키입니다. OpenAI 호환 클라이언트를 유지하기 위해 기존 변수명을 사용합니다.
- `OPENAI_BASE_URL`: Gemini OpenAI compatibility endpoint입니다.
- `OPENAI_MODEL`: 사용할 Gemini 모델입니다. 현재 기본값은 `gemini-3.1-flash-lite`입니다.

`ai.py`는 `OPENAI_API_KEY`가 없으면 `GEMINI_API_KEY`도 fallback으로 읽습니다. 따옴표가 있어도 코드에서 제거해 읽도록 처리되어 있습니다.

중요: `.env`는 API 키를 포함하므로 GitHub에 올리지 마세요.

## 5) 파일 구조

```text
mindplant/
  src/
    app.py
    ai.py
    growth.py
    storage.py
    test_growth.py
  run_app.ps1
  requirements.txt
  README.md
  design.md
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
    plants.json
```

파일 역할:

- `src/app.py`: Streamlit 화면, 페이지 흐름, 목표 완료, 챗봇 UI, 식물 아바타 렌더링
- `src/ai.py`: Gemini OpenAI 호환 API 호출, 식물 추천, 응원 메시지, 챗봇 답변 생성
- `src/growth.py`: 완료 횟수에 따른 성장 단계 계산
- `src/storage.py`: `data/demo_user.json` 기반 사용자 상태 저장/불러오기
- `data/plants.json`: 식물 메타데이터와 추천 기준
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

## 7) 배포 메모

가장 쉬운 배포 방식은 Streamlit Community Cloud입니다.

1. GitHub repository를 만듭니다.
2. `.env`, `__pycache__/`, `*.pyc`, 로컬 로그 파일은 커밋하지 않습니다.
3. Streamlit Community Cloud에서 repo와 entrypoint `src/app.py`를 선택합니다.
4. Advanced settings의 Secrets에 아래 값을 등록합니다.

```toml
OPENAI_API_KEY = "your_gemini_api_key"
OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_MODEL = "gemini-3.1-flash-lite"
```

권장 `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
.streamlit/secrets.toml
streamlit-test.log
streamlit-test.err.log
```

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
