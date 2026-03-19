# 📈 Stock Summary Bot

매일 아침 한국 증시 개장 전, 미국 시장 지표 · 코스피200 · VIX · CNN 공포·탐욕 지수 · 국내 증권 뉴스를 수집하여 **Gemini AI**가 투자 리포트로 요약한 뒤 **텔레그램**으로 자동 전송하는 봇입니다.

---

## 🤖 AI 에이전트 설계 패턴

이 프로젝트는 두 가지 AI 에이전트 설계 패턴을 채택하고 있습니다.

### 1. Sequential Pipeline Pattern (전체 파이프라인)

각 단계의 출력이 다음 단계의 입력으로 이어지는 순차 실행 구조입니다.

```
[데이터 수집] → [리포트 생성] → [구조화 추출] → [텔레그램 전송]
     ↑                ↑                ↑
  yfinance       Gemini API        Gemini API
  CNN API     + Google Search    + response_schema
  Naver 스크래핑  (Tool Grounding)   (JSON 강제 출력)
```

각 단계는 독립적인 Python 함수로 분리되어 있으며, `main.py`가 이를 오케스트레이션합니다.

### 2. Tool-Augmented Generation (리포트 생성 내부)

리포트 생성 단계에서 Gemini는 단순한 텍스트 생성에 그치지 않고 **Google Search Grounding** 도구를 자율적으로 활용합니다. 네이버 금융 뉴스 외에 추가적인 최신 정보가 필요하다고 판단하면 모델이 직접 검색을 수행하고 그 결과를 분석에 반영합니다. 이는 [ReAct](https://arxiv.org/abs/2210.03629) 패턴(Reasoning + Acting)에 가까운 동작입니다.

> **참고**: Google Search Grounding과 Structured Output(`response_schema`)은 동일 API 호출에서 함께 사용할 수 없습니다. 이 때문에 리포트 생성(Search 활성화)과 구조화 추출(schema 적용)을 별도의 Gemini 호출로 분리하는 **2단계 Sequential** 구조를 채택했습니다.

### 어제 전망 회고 (Reflection)

매일 전날의 AI 리포트(`history/YYYY-MM-DD.json`)를 읽어 오늘의 실제 시장 데이터와 비교합니다. AI가 어제의 전망이 적중했는지 스스로 평가하고 리포트에 반영하는 구조로, 에이전트 설계의 **반성(Reflection)** 패턴 요소를 포함합니다.

---

## 🔧 주요 기능

| 기능 | 설명 |
|------|------|
| 미국 시장 지표 수집 | 나스닥, S&P500, 환율(USD/KRW), 미 10년물 국채 수익률 |
| 원자재·달러 지수 수집 | WTI 원유, 금(Gold), 달러 인덱스(DXY) |
| VIX 변동성 지수 수집 | yfinance로 VIX 전일 종가 및 등락률 수집 |
| 코스피·코스닥 지수 수집 | yfinance로 전일 종가 및 등락률 수집 |
| 공포·탐욕 지수 수집 | CNN Fear & Greed API 연동, 게이지 이미지 생성 후 텔레그램 전송 |
| 국내 증권 뉴스 수집 | 네이버 금융 증권 뉴스 헤드라인 상위 15개 수집 (본문 5개 포함) |
| AI 리포트 생성 | Gemini 2.5 Flash + Google Search Grounding으로 투자 리포트 자동 생성 |
| AI 구조화 메타데이터 추출 | 리포트에서 전망 방향·확신도·핵심 리스크·주목 섹터를 JSON으로 추출 |
| 어제 전망 회고 | 전날 AI 전망과 오늘 실제 시장을 비교해 적중 여부를 리포트에 포함 |
| 히스토리 누적 | 날짜별 JSON 스냅샷 및 F&G CSV 로그 자동 저장 |
| 텔레그램 전송 | 게이지 이미지 및 리포트 텍스트를 지정된 텔레그램 채팅으로 전송 |

---

## 🗂️ 프로젝트 구조

```
stock-summary-bot/
├── main.py               # 메인 실행 파일 (데이터 수집 → AI 요약 → 텔레그램 전송)
├── fetch_market_data.py  # 미국 시장 데이터 수집 테스트 스크립트
└── requirements.txt      # 의존성 패키지 목록
```

---

## ⚙️ 환경 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

아래 환경변수를 설정해야 합니다.

| 환경변수 | 설명 |
|----------|------|
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 ([BotFather](https://t.me/BotFather)에서 발급) |
| `TELEGRAM_CHAT_IDS` | 리포트를 수신할 채팅 ID 리스트 (`123456789,987654321` 또는 `["123456789", "987654321"]`) |
| `GEMINI_API_KEY` | Google Gemini API 키 ([Google AI Studio](https://aistudio.google.com/)에서 발급) |

**Linux/macOS**
```bash
export TELEGRAM_TOKEN="your_token"
export TELEGRAM_CHAT_IDS="your_chat_id_1,your_chat_id_2"
export GEMINI_API_KEY="your_gemini_api_key"
```

**Windows (PowerShell)**
```powershell
$env:TELEGRAM_TOKEN="your_token"
$env:TELEGRAM_CHAT_IDS="your_chat_id_1,your_chat_id_2"
$env:GEMINI_API_KEY="your_gemini_api_key"
```

**GitHub Actions Secrets (권장)**
```text
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_IDS=["your_chat_id_1", "your_chat_id_2"]
GEMINI_API_KEY=your_gemini_api_key
```

`TELEGRAM_CHAT_IDS`는 쉼표 구분 문자열도 지원하지만, GitHub Actions에서는 JSON 배열 문자열 형식이 가장 안전합니다.

---

## 🚀 실행 방법

```bash
python main.py
```

---

## 🧪 E2E 스모크 테스트

실제 API 호출 및 텔레그램 발송을 포함한 전체 파이프라인을 **단일 수신자**에게만 테스트합니다.

### 로컬 실행

```bash
TEST_TELEGRAM_CHAT_ID=your_chat_id python main.py
```

`TEST_TELEGRAM_CHAT_ID`가 설정되면 `TELEGRAM_CHAT_IDS`에 등록된 전체 수신자 대신 해당 ID에게만 발송됩니다.

### GitHub Actions 수동 실행

1. GitHub 저장소의 **Settings → Secrets → Actions**에 `TEST_TELEGRAM_CHAT_ID` 시크릿을 추가합니다.
2. **Actions → Smoke Test (Single Recipient) → Run workflow**를 실행합니다.

---

## 📦 의존성

- [yfinance](https://github.com/ranaroussi/yfinance) — 미국 시장 데이터 수집
- [requests](https://docs.python-requests.org/) — HTTP 요청
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) — 웹 스크래핑
- [google-generativeai](https://github.com/google/generative-ai-python) — Gemini AI API 연동
- [matplotlib](https://matplotlib.org/) — 공포·탐욕 게이지 이미지 생성
- [numpy](https://numpy.org/) — 게이지 각도 계산

---

## 📌 참고 사항

- 네이버 금융은 구조 변경 시 스크래핑이 실패할 수 있습니다.
- CNN Fear & Greed API는 비공식 엔드포인트로, 정책 변경 시 수집이 실패할 수 있습니다.
- 한글 폰트(`Malgun Gothic`)는 Windows 전용입니다. Linux 환경에서 실행 시 한글이 깨질 수 있으므로 별도 폰트 설치가 필요합니다.
- 매일 아침 자동 실행이 필요하다면 cron 또는 GitHub Actions 스케줄러를 활용하세요.
