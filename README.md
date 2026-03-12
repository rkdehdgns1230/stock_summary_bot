# 📈 Stock Summary Bot

매일 아침 한국 증시 개장 전, 미국 시장 지표 · 코스피200 · CNN 공포·탐욕 지수 · 국내 증권 뉴스를 수집하여 **Gemini AI**가 투자 리포트로 요약한 뒤 **텔레그램**으로 자동 전송하는 봇입니다.

---

## 🔧 주요 기능

| 기능 | 설명 |
|------|------|
| 미국 시장 지표 수집 | 나스닥, S&P500, 환율(USD/KRW), 미 10년물 국채 수익률 |
| 코스피200 지수 수집 | yfinance로 코스피200 전일 종가 및 등락률 수집 |
| 공포·탐욕 지수 수집 | CNN Fear & Greed API 연동, 게이지 이미지 생성 후 텔레그램 전송 |
| 국내 증권 뉴스 수집 | 네이버 금융 증권 뉴스 헤드라인 상위 15개 수집 |
| AI 리포트 생성 | Gemini 2.5 Flash로 투자 리포트 자동 생성 |
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

---

## 🚀 실행 방법

```bash
python main.py
```

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
