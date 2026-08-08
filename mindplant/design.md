# MindPlant Design Guide (English)

This document defines the design standards needed to reproduce the current MindPlant Streamlit app. The core impression of the app is `cute pixel plant growth game`, `teen-friendly coaching`, `soft pastel background`, and `pixel UI`.

## 1) Design Concept

MindPlant is an app for working through worries, but it should not feel like a heavy counseling tool. It uses an emotional direction closer to a game UI. The user chooses a plant friend, completes small quests, and receives plant growth as a reward.

Design keywords:

- Pixel plant adventure
- Tiny quest loop
- Cute pixel HUD
- Growth reward
- Warm coaching
- Soft pastel garden

Visual direction:

- Angular pixel cards and buttons
- Thick borders and solid hard shadows
- Retro Korean typography based on DungGeunMo
- Background palette that changes by growth stage
- Real pixel-style plant PNG avatars

## 2) Typography

The primary font is `DungGeunMo`. The entire app and the chat iframe both use the same font.

```css
@font-face {
  font-family: 'DungGeunMo';
  src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
  font-weight: normal;
  font-style: normal;
}

--font-display: 'DungGeunMo', 'Press Start 2P', monospace;
--font-body: 'DungGeunMo', 'Press Start 2P', monospace;
```

Typography principles:

- Use DungGeunMo for all major text.
- Titles should be large, but not overly decorative.
- Allow long Korean text in buttons and chips to wrap safely using `white-space: normal`, `overflow-wrap: anywhere`, and `word-break: keep-all`.
- Keep letter spacing slightly open.

Key sizes:

- H1: `clamp(2.08rem, 6.2vw, 3.24rem)`, line-height `1.28`
- H2: `clamp(1.38rem, 4.2vw, 2.05rem)`, line-height `1.4`
- Body: `clamp(0.94rem, 1.2vw, 1.05rem)`, line-height `1.72`
- Chat bubble: `0.88rem`, line-height `1.55`

## 3) Color System

### Core Tokens

```css
--pixel-ink: #183146;
--pixel-mint: #9FE8AF;
--pixel-lime: #62D484;
--pixel-cream: #FFF6D3;
--pixel-peach: #FFC58E;
--pixel-sky: #87D2FF;
--pixel-shadow: #122538;
```

Roles:

- `#183146`: Main borders and default text
- `#122538`: Pixel shadows
- `#FFF6D3`: Bright cream chips and labels
- `#9FE8AF`, `#62D484`: Mint/lime accents for early growth stages
- `#87D2FF`: Secondary sky blue
- `#FFC58E`: Warm accent for later growth stages

### Growth Theme Palettes

The app background and accent colors change according to the growth level derived from completed goals.

| Level | Stage | bg_top | bg_mid | bg_bottom | accent | accent_soft | chip |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Seed | `#C7F5D3` | `#DFF8E6` | `#F6FFDF` | `#62D484` | `#9FE8AF` | `#FFF6D3` |
| 2 | Sprout | `#B7F3DB` | `#D2F9EE` | `#ECFFE6` | `#50C6A6` | `#92E6CF` | `#FFF5C3` |
| 3 | Young Leaf | `#B6EEEC` | `#D6F8F6` | `#EEFEE8` | `#49B1C8` | `#88D5E4` | `#FFE6BF` |
| 4 | Stem | `#BDE4FF` | `#D9EEFF` | `#F2F7E8` | `#5C8BFF` | `#9FB9FF` | `#FFD9B3` |
| 5 | Flower | `#FFDDBA` | `#FFEED4` | `#FFF6DC` | `#FF9B55` | `#FFC58E` | `#FFEAA1` |

## 4) Background

The overall app background combines pastel gradients and a pixel grid pattern.

Composition:

- 18px semi-transparent white pixel grid
- Peach circular highlight in the upper-left
- Sky-blue circular highlight in the upper-right
- Vertical growth-stage gradient from `bg_top → bg_mid → bg_bottom`
- `background-attachment: fixed`

Design intent:

- Make the experience feel closer to a game start screen than a static counseling app.
- Keep the background bright while preserving information hierarchy through thick card and button borders.

## 5) Layout

Main container:

```css
.block-container {
  max-width: 1040px;
  padding-top: 1.5rem;
  padding-bottom: 3.2rem;
}
```

Page structure:

- Start: Hero card centered around the core app identity
- Concern: Worry selection card
- Survey: Five sliders and a free-text input
- Recommendation: Recommended plant card and three starter goals
- Home: Growth plant on the left, chatbot on the right, goal input below

Home column ratio:

```python
left_col, right_col = st.columns([1.28, 0.92], gap="medium")
```

The left side handles plant growth reward, and the right side handles the chatbot.

## 6) Cards And Panels

Common card style:

```css
border: 3px solid var(--pixel-ink);
border-radius: 0;
box-shadow: 6px 6px 0 var(--pixel-shadow);
padding: 1.38rem 1.42rem;
```

Principles:

- Do not use rounded corners.
- Use hard shadows without blur.
- Keep enough internal padding.
- Avoid excessive nested decorative cards inside cards.

Main cards:

- `.hero-box`: Main card on the start screen
- `.plant-card`: Recommendation result card
- `.grow-focus`: Plant growth card on the home screen
- `.chat-card`: Plant friend chat box

## 7) Buttons

Streamlit default buttons are restyled as pixel buttons.

```css
.stButton > button {
  min-height: 3.55rem;
  border-radius: 0;
  border: 3px solid var(--pixel-ink);
  border-bottom-width: 5px;
  background: linear-gradient(180deg, var(--theme-accent) 0%, var(--theme-accent-soft) 100%);
  color: var(--pixel-ink);
  font-family: var(--font-display);
  box-shadow: 4px 4px 0 var(--pixel-shadow);
}
```

Interactions:

- Hover: Move the button 1px up-left and increase the shadow.
- Active: Move the button 2px down-right and reduce the shadow.
- Form submit buttons use a light blue palette to distinguish them.

## 8) Chips, Badges, And Labels

`goal-chip` is used like a small game HUD badge.

```css
.goal-chip {
  display: inline-flex;
  border: 2px solid var(--pixel-ink);
  border-radius: 0;
  box-shadow: 2px 2px 0 var(--pixel-shadow);
  background: var(--theme-chip);
  font-family: var(--font-display);
}
```

Usage:

- Start screen: `TINY QUEST LOOP`, `CUTE PIXEL HUD`, `GROWTH REWARD`
- Concern screen: Example worry chips
- Home screen: Feature summary chips

`stage-pill` is the status label that shows the current plant stage and level.

Format:

```text
STAGE Seed · Lv.1
```

In the Korean UI, stage names are displayed in Korean, such as `STAGE 씨앗 · Lv.1`.

## 9) Goal Rows

The starter goals in the recommendation result are displayed as three goal rows.

Style:

- 2px dark border
- Light mint background `#ECFFF4`
- 3px hard shadow
- Number badge on the left
- Goal text on the right

Intent:

- Make goals feel like “quest items” rather than a plain list.

## 10) Plant Avatars

Plant images use PNG files from `assets/plants`.

File convention:

```text
plant_id.png
plant_id_lv1.png
plant_id_lv2.png
plant_id_lv3.png
plant_id_lv4.png
plant_id_lv5.png
```

Examples:

```text
basil_lv1.png
basil_lv5.png
sunflower_lv3.png
```

Image rendering principles:

- Apply `image-rendering: pixelated`.
- Center align images.
- Prefer growth-level-specific images.
- Fallback to the base image if a stage-specific image is missing.
- In plant cards, the real PNG avatar should be the strongest visual signal.

Avatar sizes:

- Start/Recommendation: `avatar-lg`, display width around 450px
- Home growth card: `avatar-md`, display width around 515px

## 11) Chat UI

The chat box is rendered as independent HTML inside `st.iframe`. This is done to make automatic scrolling to the bottom stable after message input.

Chat card:

```css
.chat-card {
  height: 26rem;
  padding: 1rem 1rem 0.9rem;
  border: 3px solid #183146;
  background: linear-gradient(180deg, #FDFEFF 0%, #EAF5FF 100%);
  box-shadow: 6px 6px 0 rgba(24, 49, 70, 0.28);
}
```

Chat log:

```css
.chat-log {
  display: flex;
  flex-direction: column;
  gap: 0.46rem;
  overflow-y: auto;
  overflow-x: hidden;
}
```

Bubbles:

- Bot: Left aligned, white background `#FFFFFF`, text `#17334A`
- User: Right aligned, yellow cream background `#FFF4BF`, text `#1F3B47`
- Shared: 2px border, 2px hard shadow, pre-wrap

Automatic chat scroll:

- When a message is added, set `#mindplant-chat-log`'s `scrollTop` to `scrollHeight`.
- Use `requestAnimationFrame`, `setTimeout`, and `MutationObserver` together to account for Streamlit rerun render timing.

## 12) Inputs

Text inputs and textareas use a bright cream background with pixel borders.

```css
.stTextInput input,
.stTextArea textarea {
  background: #FFFDF4;
  border: 2px solid var(--pixel-ink);
  border-radius: 0;
  box-shadow: inset 2px 2px 0 rgba(24, 49, 70, 0.2);
  color: #111111;
}
```

Placeholder:

```css
color: #4A6276;
```

## 13) Growth Feedback

When a goal is completed:

- Increment completed count
- Recalculate plant level
- Update plant avatar
- Show an encouragement message
- Display a particle burst effect

Growth stages:

| Completed Count | Stage | Level | Message |
| --- | --- | --- | --- |
| 0 | Seed | 1 | 아직 작은 가능성이 잠들어 있어요 |
| 1-2 | Sprout | 2 | 첫 실천으로 싹이 텄어요 |
| 3-4 | Young Leaf | 3 | 꾸준함이 보이기 시작했어요 |
| 5-7 | Stem | 4 | 스스로를 믿는 힘이 자라고 있어요 |
| 8+ | Flower | 5 | 작은 목표들이 멋진 변화가 되었어요 |

The UI currently displays the Korean stage names and messages.

## 14) Page Copy Tone

Copy should be short, warm, and low-pressure for teen users.

Principles:

- Do not blame the user.
- Do not sound like a diagnosis.
- Suggest small next actions instead of huge commitments.
- Use light game language such as “quest,” “growth,” and “plant friend.”

Representative copy:

```text
내 마음을 이해하는 AI 식물 친구
작은 퀘스트를 완료하며 식물 친구를 키우는 귀여운 도트 감성 성장 게임
오늘의 목표를 달성할 때마다 경험치가 쌓이고 식물이 성장해요
목표 추천이 필요하면 '오늘 목표 추천해줘'라고 말해줘.
```

## 15) Responsive Notes

On mobile or narrow screens, preserve the following:

- Reduce card padding.
- Lower chat box height to about 22rem.
- Allow button text to wrap.
- Limit title size with clamp.
- Constrain image display width so it does not overflow the parent.
- Keep `overflow-wrap` so text does not spill out of buttons or chips.

## 16) Implementation Notes

Streamlit implementation notes:

- Inject global CSS with `st.markdown(..., unsafe_allow_html=True)`.
- Render the chat box as `st.iframe` HTML because it needs automatic scrolling.
- Do not use `st.components.v1.html`.
- `requirements.txt` must require Streamlit `1.59.2` or newer.
- CSS from the parent app does not cascade into the chat iframe, so declare the `DungGeunMo` font again inside the iframe.
- Keep `image-rendering: pixelated` so PNG plant assets remain crisp.

## 17) Do Not Change Without Intent

To preserve the design identity, avoid changing these elements casually:

- `DungGeunMo` font
- Angular 0-radius cards and buttons
- 2-3px dark borders
- 4-6px hard shadows
- Growth-stage pastel palettes
- Pixel plant PNG avatars
- Copy centered around quests, growth, and plant friends

---

# MindPlant Design Guide

이 문서는 현재 구현된 MindPlant Streamlit 앱의 디자인을 재현하기 위한 기준입니다. 앱의 핵심 인상은 `귀여운 픽셀 식물 성장 게임`, `청소년 친화적 코칭`, `부드러운 파스텔 배경`, `도트 UI`입니다.

## 1) 디자인 콘셉트

MindPlant는 고민 해결 앱이지만, 무거운 상담 도구처럼 보이지 않도록 게임 UI에 가까운 감성을 사용합니다. 사용자는 식물 친구를 고르고, 작은 퀘스트를 완료하며, 식물의 성장으로 보상을 받습니다.

디자인 키워드:

- Pixel plant adventure
- Tiny quest loop
- Cute pixel HUD
- Growth reward
- Warm coaching
- Soft pastel garden

시각적 방향:

- 각진 픽셀 카드와 버튼
- 두꺼운 테두리와 단단한 그림자
- 둥근모 기반의 레트로 한글 타이포
- 성장 단계에 따라 변하는 배경 팔레트
- 실제 식물 도트 PNG 아바타 사용

## 2) Typography

기본 폰트는 `DungGeunMo`입니다. 앱 전체와 채팅 iframe 내부 모두 같은 폰트를 사용합니다.

```css
@font-face {
  font-family: 'DungGeunMo';
  src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_six@1.2/DungGeunMo.woff') format('woff');
  font-weight: normal;
  font-style: normal;
}

--font-display: 'DungGeunMo', 'Press Start 2P', monospace;
--font-body: 'DungGeunMo', 'Press Start 2P', monospace;
```

타입 원칙:

- 모든 주요 텍스트는 둥근모로 통일한다.
- 제목은 크게 쓰되 과하게 장식하지 않는다.
- 한글이 긴 버튼/칩 안에서 잘리지 않도록 `white-space: normal`, `overflow-wrap: anywhere`, `word-break: keep-all`을 사용한다.
- 글자 간격은 약간 넓게 둔다.

주요 크기:

- H1: `clamp(2.08rem, 6.2vw, 3.24rem)`, line-height `1.28`
- H2: `clamp(1.38rem, 4.2vw, 2.05rem)`, line-height `1.4`
- 본문: `clamp(0.94rem, 1.2vw, 1.05rem)`, line-height `1.72`
- 채팅 말풍선: `0.88rem`, line-height `1.55`

## 3) Color System

### Core Tokens

```css
--pixel-ink: #183146;
--pixel-mint: #9FE8AF;
--pixel-lime: #62D484;
--pixel-cream: #FFF6D3;
--pixel-peach: #FFC58E;
--pixel-sky: #87D2FF;
--pixel-shadow: #122538;
```

역할:

- `#183146`: 모든 주요 테두리와 기본 텍스트
- `#122538`: 픽셀 그림자
- `#FFF6D3`: 밝은 크림 칩/라벨
- `#9FE8AF`, `#62D484`: 초기 성장 단계의 민트/라임 포인트
- `#87D2FF`: 보조 하늘색
- `#FFC58E`: 성장 후반부의 따뜻한 포인트

### Growth Theme Palettes

앱 배경과 포인트 컬러는 완료 횟수에 따른 성장 레벨로 변경됩니다.

| Level | Stage | bg_top | bg_mid | bg_bottom | accent | accent_soft | chip |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 씨앗 | `#C7F5D3` | `#DFF8E6` | `#F6FFDF` | `#62D484` | `#9FE8AF` | `#FFF6D3` |
| 2 | 새싹 | `#B7F3DB` | `#D2F9EE` | `#ECFFE6` | `#50C6A6` | `#92E6CF` | `#FFF5C3` |
| 3 | 어린잎 | `#B6EEEC` | `#D6F8F6` | `#EEFEE8` | `#49B1C8` | `#88D5E4` | `#FFE6BF` |
| 4 | 줄기 | `#BDE4FF` | `#D9EEFF` | `#F2F7E8` | `#5C8BFF` | `#9FB9FF` | `#FFD9B3` |
| 5 | 꽃 | `#FFDDBA` | `#FFEED4` | `#FFF6DC` | `#FF9B55` | `#FFC58E` | `#FFEAA1` |

## 4) Background

앱 전체 배경은 파스텔 그라데이션과 픽셀 격자 패턴을 겹쳐 사용합니다.

구성:

- 18px 간격의 흰색 반투명 픽셀 그리드
- 좌상단 복숭아색 원형 하이라이트
- 우상단 하늘색 원형 하이라이트
- 성장 단계별 `bg_top → bg_mid → bg_bottom` 세로 그라데이션
- `background-attachment: fixed`

디자인 의도:

- 정적인 상담 앱보다 게임 시작 화면 같은 느낌을 준다.
- 배경은 밝지만 카드/버튼의 두꺼운 테두리로 정보 계층을 유지한다.

## 5) Layout

전체 컨테이너:

```css
.block-container {
  max-width: 1040px;
  padding-top: 1.5rem;
  padding-bottom: 3.2rem;
}
```

페이지 구조:

- Start: 히어로 카드 중심
- Concern: 고민 선택 카드
- Survey: 슬라이더 5개와 자유 입력
- Recommendation: 추천 식물 카드와 시작 목표 3개
- Home: 좌측 성장 식물, 우측 챗봇, 하단 목표 입력

Home 화면 컬럼 비율:

```python
left_col, right_col = st.columns([1.28, 0.92], gap="medium")
```

좌측은 식물 성장 보상, 우측은 챗봇을 담당합니다.

## 6) Cards And Panels

공통 카드 스타일:

```css
border: 3px solid var(--pixel-ink);
border-radius: 0;
box-shadow: 6px 6px 0 var(--pixel-shadow);
padding: 1.38rem 1.42rem;
```

원칙:

- 둥근 모서리를 쓰지 않는다.
- 그림자는 흐림 없는 하드 섀도우를 쓴다.
- 카드 내부 여백은 충분히 둔다.
- 카드 안에 또 다른 장식 카드가 과하게 중첩되지 않게 한다.

주요 카드:

- `.hero-box`: 시작 화면의 메인 카드
- `.plant-card`: 추천 결과 카드
- `.grow-focus`: 홈 화면의 식물 성장 카드
- `.chat-card`: 식물 친구 대화 박스

## 7) Buttons

Streamlit 기본 버튼을 픽셀 버튼처럼 재스타일링합니다.

```css
.stButton > button {
  min-height: 3.55rem;
  border-radius: 0;
  border: 3px solid var(--pixel-ink);
  border-bottom-width: 5px;
  background: linear-gradient(180deg, var(--theme-accent) 0%, var(--theme-accent-soft) 100%);
  color: var(--pixel-ink);
  font-family: var(--font-display);
  box-shadow: 4px 4px 0 var(--pixel-shadow);
}
```

상호작용:

- Hover: 버튼이 좌상단으로 1px 이동하고 그림자가 커진다.
- Active: 버튼이 우하단으로 2px 눌리고 그림자가 작아진다.
- Form submit 버튼은 연한 파란색 계열로 구분한다.

## 8) Chips, Badges, And Labels

`goal-chip`은 작은 게임 HUD 배지처럼 사용합니다.

```css
.goal-chip {
  display: inline-flex;
  border: 2px solid var(--pixel-ink);
  border-radius: 0;
  box-shadow: 2px 2px 0 var(--pixel-shadow);
  background: var(--theme-chip);
  font-family: var(--font-display);
}
```

사용 위치:

- Start 화면의 `TINY QUEST LOOP`, `CUTE PIXEL HUD`, `GROWTH REWARD`
- Concern 화면의 고민 예시
- Home 화면의 기능 요약

`stage-pill`은 현재 식물 단계와 레벨을 보여주는 상태 라벨입니다.

형식:

```text
STAGE 씨앗 · Lv.1
```

## 9) Goal Rows

추천 결과의 시작 목표는 3개 goal row로 표시합니다.

스타일:

- 2px 진한 테두리
- 연한 민트 배경 `#ECFFF4`
- 3px 하드 섀도우
- 좌측에 번호 배지
- 우측에 목표 텍스트

의도:

- 목표를 일반 목록이 아니라 “퀘스트 항목”처럼 보이게 한다.

## 10) Plant Avatars

식물 이미지는 `assets/plants`의 PNG를 사용합니다.

파일 규칙:

```text
plant_id.png
plant_id_lv1.png
plant_id_lv2.png
plant_id_lv3.png
plant_id_lv4.png
plant_id_lv5.png
```

예시:

```text
basil_lv1.png
basil_lv5.png
sunflower_lv3.png
```

이미지 렌더링 원칙:

- `image-rendering: pixelated` 적용
- 중앙 정렬
- 성장 레벨별 이미지 우선 사용
- 단계별 이미지가 없으면 기본 이미지로 fallback
- 식물 카드 안에서는 실제 PNG 아바타가 가장 강한 시각 신호가 되도록 한다.

아바타 크기:

- Start/Recommendation: `avatar-lg`, display width 약 450px
- Home growth card: `avatar-md`, display width 약 515px

## 11) Chat UI

채팅 박스는 `st.iframe` 안에 독립 HTML로 렌더링합니다. 이유는 메시지 입력 후 자동 하단 스크롤을 안정적으로 구현하기 위해서입니다.

채팅 박스:

```css
.chat-card {
  height: 26rem;
  padding: 1rem 1rem 0.9rem;
  border: 3px solid #183146;
  background: linear-gradient(180deg, #FDFEFF 0%, #EAF5FF 100%);
  box-shadow: 6px 6px 0 rgba(24, 49, 70, 0.28);
}
```

채팅 로그:

```css
.chat-log {
  display: flex;
  flex-direction: column;
  gap: 0.46rem;
  overflow-y: auto;
  overflow-x: hidden;
}
```

말풍선:

- Bot: 좌측 정렬, 흰색 배경 `#FFFFFF`, 텍스트 `#17334A`
- User: 우측 정렬, 노란 크림 배경 `#FFF4BF`, 텍스트 `#1F3B47`
- 공통: 2px 테두리, 2px 하드 섀도우, pre-wrap

채팅 자동 스크롤:

- 메시지가 추가되면 `#mindplant-chat-log`의 `scrollTop`을 `scrollHeight`로 설정한다.
- `requestAnimationFrame`, `setTimeout`, `MutationObserver`를 함께 사용해 Streamlit rerun 이후 렌더 타이밍 차이를 보정한다.

## 12) Inputs

Text input과 textarea는 밝은 크림 배경과 픽셀 테두리를 사용합니다.

```css
.stTextInput input,
.stTextArea textarea {
  background: #FFFDF4;
  border: 2px solid var(--pixel-ink);
  border-radius: 0;
  box-shadow: inset 2px 2px 0 rgba(24, 49, 70, 0.2);
  color: #111111;
}
```

Placeholder:

```css
color: #4A6276;
```

## 13) Growth Feedback

목표 완료 시:

- 완료 횟수 증가
- 식물 레벨 재계산
- 식물 아바타 갱신
- 응원 메시지 출력
- particle burst 효과 표시

성장 단계:

| Completed Count | Stage | Level | Message |
| --- | --- | --- | --- |
| 0 | 씨앗 | 1 | 아직 작은 가능성이 잠들어 있어요 |
| 1-2 | 새싹 | 2 | 첫 실천으로 싹이 텄어요 |
| 3-4 | 어린잎 | 3 | 꾸준함이 보이기 시작했어요 |
| 5-7 | 줄기 | 4 | 스스로를 믿는 힘이 자라고 있어요 |
| 8+ | 꽃 | 5 | 작은 목표들이 멋진 변화가 되었어요 |

## 14) Page Copy Tone

문구는 청소년에게 부담을 주지 않는 짧고 따뜻한 톤을 사용합니다.

원칙:

- 비난하지 않는다.
- 진단처럼 말하지 않는다.
- 큰 결심보다 작은 다음 행동을 제안한다.
- “퀘스트”, “성장”, “식물 친구”처럼 가벼운 게임 언어를 사용한다.

대표 문구:

```text
내 마음을 이해하는 AI 식물 친구
작은 퀘스트를 완료하며 식물 친구를 키우는 귀여운 도트 감성 성장 게임
오늘의 목표를 달성할 때마다 경험치가 쌓이고 식물이 성장해요
목표 추천이 필요하면 '오늘 목표 추천해줘'라고 말해줘.
```

## 15) Responsive Notes

모바일/좁은 화면에서는 다음을 유지해야 합니다.

- 카드 padding을 줄인다.
- 채팅 박스 높이는 약 22rem로 낮춘다.
- 버튼 텍스트는 줄바꿈을 허용한다.
- 제목 크기는 clamp로 제한한다.
- 이미지가 부모 영역을 넘지 않도록 display width를 제한한다.
- 텍스트가 버튼/칩 밖으로 넘치지 않게 `overflow-wrap`을 유지한다.

## 16) Implementation Notes

Streamlit 구현 시 주의할 점:

- 전역 CSS는 `st.markdown(..., unsafe_allow_html=True)`로 주입한다.
- 채팅 박스는 자동 스크롤 때문에 `st.iframe` HTML로 렌더링한다.
- `st.components.v1.html`은 사용하지 않는다.
- `requirements.txt`의 Streamlit 최소 버전은 `1.59.2` 이상이어야 한다.
- 채팅 iframe 내부에는 부모 CSS가 상속되지 않으므로 `DungGeunMo` 폰트를 iframe 내부에서도 다시 선언해야 한다.
- PNG 식물 이미지는 픽셀 아트가 흐려지지 않도록 `image-rendering: pixelated`를 유지한다.

## 17) Do Not Change Without Intent

디자인 정체성을 유지하려면 아래 요소는 쉽게 바꾸지 않습니다.

- `DungGeunMo` 폰트
- 각진 0 radius 카드와 버튼
- 2-3px 진한 테두리
- 4-6px 하드 섀도우
- 성장 단계별 파스텔 팔레트
- 도트 식물 PNG 아바타
- 퀘스트/성장/식물 친구 중심의 문구
