import os
import re
from datetime import datetime, timezone, timedelta
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from google import genai
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import numpy as np
import io

def _get_korean_font() -> fm.FontProperties:
    """OS별 한글 폰트 자동 선택 (Malgun Gothic → NanumGothic → 기본 폰트 순)"""
    available = {f.name for f in fm.fontManager.ttflist}
    for name in ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'NanumBarunGothic']:
        if name in available:
            return fm.FontProperties(family=name)
    return fm.FontProperties()

# 1. 설정 (환경변수 사용)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

def get_us_market():
    """미국 증시 주요 지표 수집"""
    tickers = {
        "나스닥": "^IXIC",
        "S&P500": "^GSPC",
        "환율(USD/KRW)": "KRW=X",
        "미10년물국채": "^TNX"
    }
    market_results = []
    for name, ticker in tickers.items():
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            close = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            change_pct = ((close - prev_close) / prev_close) * 100
            market_results.append(f"{name}: {close:.2f} ({change_pct:+.2f}%)")
    return "\n".join(market_results)

def get_kospi_futures():
    """코스피 200 지수 수집 (yfinance)"""
    try:
        print("[코스피200] yfinance로 데이터 요청 중...")
        data = yf.Ticker("^KS200").history(period="2d")
        print(f"[코스피200] 수신된 데이터 행 수: {len(data)}")

        if len(data) < 2:
            print(f"[코스피200] 데이터 부족: {data}")
            return "코스피200: 데이터 부족"

        close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        change_pct = ((close - prev_close) / prev_close) * 100
        result = f"코스피200: {close:.2f} ({change_pct:+.2f}%)"
        print(f"[코스피200] 수집 완료: {result}")
        return result
    except Exception as e:
        print(f"[코스피200] 예외 발생: {type(e).__name__}: {e}")
        return "코스피200: 정보 가져오기 실패"

def get_naver_finance_news():
    """네이버 금융 증권 뉴스 수집"""
    url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        print(f"[네이버금융] 뉴스 목록 요청: {url}")
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        print(f"[네이버금융] 응답 코드: {res.status_code}")

        if res.status_code != 200:
            print(f"[네이버금융] 비정상 응답 본문(앞 500자):\n{res.text[:500]}")
            return f"뉴스 수집 실패: HTTP {res.status_code}"

        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('dd.articleSubject a')[:15]
        print(f"[네이버금융] 파싱된 기사 수: {len(articles)}")

        if not articles:
            print(f"[네이버금융] 기사 파싱 실패 - 응답 본문(앞 1000자):\n{res.text[:1000]}")
            return "뉴스 수집 실패: 기사 파싱 실패"

        results = []
        for i, article in enumerate(articles):
            title = article.get_text(strip=True)
            print(f"[네이버금융] 기사 #{i+1}: {title}")
            results.append(title)

        print(f"[네이버금융] 최종 수집된 기사 수: {len(results)}")
        return "\n".join(f"- {t}" for t in results)
    except Exception as e:
        print(f"[네이버금융] 예외 발생: {type(e).__name__}: {e}")
        return f"뉴스 수집 실패: {e}"

RATING_KO = {
    "extreme fear": "극도의 공포",
    "fear": "공포",
    "neutral": "중립",
    "greed": "탐욕",
    "extreme greed": "극도의 탐욕",
}

def get_fear_and_greed_score() -> int:
    """CNN 주식시장 공포·탐욕 지수 수집"""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://edition.cnn.com/",
        "Origin": "https://edition.cnn.com",
    }
    try:
        print("[공포와탐욕] CNN Fear & Greed 지수 요청 중...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()["fear_and_greed"]
        score = round(data["score"])
        rating_en = data["rating"]
        rating_ko = RATING_KO.get(rating_en, rating_en)
        prev_close = round(data["previous_close"])
        result = f"공포·탐욕 지수: {score}/100 ({rating_ko}) | 전일: {prev_close}"
        print(f"[공포와탐욕] 수집 완료: {result}")
        return score
    except Exception as e:
        print(f"[공포와탐욕] 예외 발생: {type(e).__name__}: {e}")
        return -1

def generate_fear_greed_gauge_image(score):
    """공포·탐욕 지수 반원 게이지 이미지 생성 (직교좌표 기반)"""
    fp = _get_korean_font()

    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor('white')
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-0.65, 1.45)
    ax.set_aspect('equal')
    ax.axis('off')

    # 색상 세그먼트: (시작점수, 끝점수, 색상, 라벨)
    # 각도 변환: score=0 → 180°(좌), score=100 → 0°(우)
    OUTER_R = 1.0
    INNER_R = 0.55
    segments = [
        (0,   25,  '#d32f2f', '극도의\n공포'),
        (25,  45,  '#FF8C00', '공포'),
        (45,  55,  '#F9A825', '중립'),
        (55,  75,  '#7CB342', '탐욕'),
        (75,  100, '#2E7D32', '극도의\n탐욕'),
    ]

    for start_s, end_s, color, label in segments:
        # patches.Wedge는 직교좌표계 → theta1 < theta2 순서여야 함
        theta1 = 180 - end_s * 1.8
        theta2 = 180 - start_s * 1.8
        ax.add_patch(patches.Wedge(
            center=(0, 0), r=OUTER_R,
            theta1=theta1, theta2=theta2,
            width=OUTER_R - INNER_R,
            facecolor=color, edgecolor='white', linewidth=2,
        ))

        # 세그먼트 바깥쪽에 라벨 배치
        mid_angle = np.deg2rad(180 - (start_s + end_s) / 2 * 1.8)
        label_r = OUTER_R + 0.25
        ax.text(
            label_r * np.cos(mid_angle),
            label_r * np.sin(mid_angle),
            label, fontproperties=fp,
            ha='center', va='center', fontsize=9, color='#222222', linespacing=1.3,
        )

    # 내부 눈금 숫자 (0, 25, 50, 75, 100)
    for tick in [0, 25, 50, 75, 100]:
        tick_angle = np.deg2rad(180 - tick * 1.8)
        tick_r = INNER_R - 0.12
        ax.text(
            tick_r * np.cos(tick_angle),
            tick_r * np.sin(tick_angle),
            str(tick), ha='center', va='center', fontsize=8, color='#666666',
        )

    # 바늘
    needle_angle = np.deg2rad(180 - score * 1.8)
    needle_len = OUTER_R - 0.04
    ax.plot(
        [0, needle_len * np.cos(needle_angle)],
        [0, needle_len * np.sin(needle_angle)],
        color='#1a1a1a', lw=3, solid_capstyle='round', zorder=4,
    )
    ax.add_patch(plt.Circle((0, 0), 0.07, color='#1a1a1a', zorder=5))

    # 점수 (대형)
    ax.text(0, -0.2, str(score), ha='center', va='center',
            fontproperties=fp, fontsize=44, fontweight='bold', color='#1a1a1a')

    # 단계 텍스트
    ax.text(0, -0.48, get_fng_description(score), ha='center', va='center',
            fontproperties=fp, fontsize=12, color='#555555')

    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', bbox_inches='tight', dpi=150, facecolor='white')
    img_data.seek(0)
    plt.close(fig)
    return img_data

def get_fng_description(score):
    if score < 25:
        return "극도의 공포 (Extreme Fear)"
    elif score < 45:
        return "공포 (Fear)"
    elif score < 55:
        return "중립 (Neutral)"
    elif score < 75:
        return "탐욕 (Greed)"
    else:
        return "극도의 탐욕 (Extreme Greed)"

def get_persona_instruction(score):
    """지수 점수에 따라 시스템 지침(System Instruction)을 반환"""
    if score < 25:
        return "너는 지금 시장이 붕괴될까 봐 공포에 질린 '겁쟁이 투자자'야. 모든 지표를 부정적으로 해석하고, 당장 도망가야 한다고 벌벌 떨며 말해줘."
    elif score < 45:
        return "너는 아주 보수적인 '염세주의 분석가'야. 상승장 속에서도 숨은 위험을 찾아내고, 독설을 섞어가며 조심하라고 경고해."
    elif score < 55:
        return "너는 감정이 없는 '퀀트 분석 로봇'이야. 철저하게 수치와 팩트 중심으로만, 군더더기 없이 딱딱하게 보고해."
    elif score < 75:
        return "너는 에너지가 넘치는 '낙관주의 트레이더'야. 시장의 기회를 강조하고, 투자자들에게 희망과 자신감을 주는 말투를 사용해."
    else:
        return "너는 지금 탐욕에 눈이 먼 '광기 어린 투기꾼'이야. 무조건 상승한다고 외치고, 이모지를 남발하며 매우 흥분된 상태로 가즈아를 외쳐!"

def sanitize_for_telegram_mdv2(text: str) -> str:
    """
    MarkdownV2 sanitizer. 지원 포맷:
    *bold*, _italic_, __underline__, ~~strikethrough~~, ||spoiler||,
    `inline code`, ```code block```, >blockquote
    포맷팅 스팬은 내부 특수문자만 이스케이프하고 구분자는 보존.
    일반 텍스트는 MarkdownV2 특수문자를 전체 이스케이프.
    """
    PLAIN_ESCAPE_RE = re.compile(r'(?<!\\)([_*.\-+()~!=#>|{}\[\]])')
    INNER_ESCAPE_RE = re.compile(r'(?<!\\)([.\-+()!=#>{}\[\]])')

    protected = []

    def protect(content):
        idx = len(protected)
        protected.append(content)
        return f'\x00{idx}\x00'

    # 1. 코드 블록 우선 보호 (내부 이스케이프 없음)
    text = re.sub(r'```[\s\S]*?```', lambda m: protect(m.group()), text)

    # 2. 인라인 포맷팅 스팬 보호 (긴 구분자 우선 매칭)
    INLINE_RE = re.compile(
        r'__[^_\n]+?__'      # __underline__
        r'|\*[^*\n]+?\*'     # *bold*
        r'|_[^_\n]+?_'       # _italic_
        r'|~~[^\n]+?~~'      # ~~strikethrough~~
        r'|\|\|[^\n]+?\|\|'  # ||spoiler||
        r'|`[^`\n]+?`'       # `inline code`
    )

    def replace_inline(m):
        span = m.group()
        if span.startswith('__'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('__' + inner + '__')
        if span.startswith('~~'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('~~' + inner + '~~')
        if span.startswith('||'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('||' + inner + '||')
        if span.startswith('*'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[1:-1])
            return protect('*' + inner + '*')
        if span.startswith('_'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[1:-1])
            return protect('_' + inner + '_')
        return protect(span)  # `inline code`: 이스케이프 없이 보호

    text = INLINE_RE.sub(replace_inline, text)

    # 3. 일반 텍스트 이스케이프 (blockquote 줄은 > 접두어 보존)
    lines = text.split('\n')
    escaped = []
    for line in lines:
        if line.startswith('>'):
            escaped.append('>' + PLAIN_ESCAPE_RE.sub(r'\\\1', line[1:]))
        else:
            escaped.append(PLAIN_ESCAPE_RE.sub(r'\\\1', line))
    text = '\n'.join(escaped)

    # 4. 보호된 스팬 복원
    for i, p in enumerate(protected):
        text = text.replace(f'\x00{i}\x00', p)
    return text

def summarize_and_send():
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y년 %m월 %d일")

    score = get_fear_and_greed_score()
    fng_stage = get_fng_description(score)
    gauge_image = generate_fear_greed_gauge_image(score)
    print("[데이터 수집] 공포·탐욕 지수:\n", score)

    us_data = get_us_market()
    print("[데이터 수집] 미국 시장 지표:\n", us_data)

    kospi_data = get_kospi_futures()
    print("[데이터 수집] 코스피200 야간선물:\n", kospi_data)

    news_data = get_naver_finance_news()
    print("[데이터 수집] 네이버 금융 뉴스:\n", news_data[:300], "...")

    persona_instruction = get_persona_instruction(score)

    # Gemini 프롬프트 구성
    prompt = f"""
[페르소나]
{persona_instruction}
위 페르소나에 완전히 몰입하여, 전체 리포트의 문체와 어조를 이 캐릭터로 일관되게 유지해라.

[임무]
오늘({today}) 아침 한국 주식시장 개장 전, 투자자를 위한 *모닝 브리핑 리포트*를 작성해야 한다.
아래 데이터는 자동 수집된 것으로 일부 항목이 누락되거나 "데이터 부족", "수집 실패" 상태일 수 있다.
*누락·실패 항목은 절대 "데이터 없음"으로 건너뛰지 말고*, 나머지 지표들 간의 상관관계와 시장 맥락을 활용해 합리적으로 추론하여 최선의 분석을 제공해야 한다.

[입력 데이터]
1. 미국 시장 지표 (전일 종가 기준):
{us_data}

2. 코스피200 지수 (전일 종가 기준):
{kospi_data}

3. CNN 공포·탐욕 지수: {fng_stage} ({score}/100)
   - 0~24: 극도의 공포 / 25~44: 공포 / 45~55: 중립 / 56~75: 탐욕 / 76~100: 극도의 탐욕

4. 국내 증권 주요 뉴스 (네이버 금융):
{news_data}

[분석 사고 흐름 — 반드시 이 순서로 내부적으로 추론한 뒤 리포트를 작성해라]
Step 1. 미국 지수(나스닥·S&P500)의 방향성과 변동폭이 한국 시장에 주는 선행 시그널을 파악한다.
Step 2. 환율(USD/KRW)과 미 10년물 국채 금리가 외국인 자금 흐름 및 성장주 밸류에이션에 미치는 영향을 판단한다.
Step 3. 공포·탐욕 지수가 현재 시장 심리의 과열·공포 구간 여부를 나타내는지 해석하고, 반전 가능성을 고려한다.
Step 4. 뉴스 헤드라인에서 당일 한국 증시에 직접 영향을 줄 핵심 이슈(정책, 실적, 지정학적 리스크 등)를 추출한다.
Step 5. 위 네 가지 요소를 종합하여 오늘 코스피 및 코스닥의 상승/하락 가능성과 강도를 결론 짓는다.
Step 6. 특정 데이터가 누락된 경우, 다른 지표들을 근거로 삼아 그 항목을 최대한 추론·보완한다.

[출력 구조 — 아래 6개 섹션을 순서대로 작성할 것]
- 섹션 헤더는 반드시 __이모지 헤더텍스트__ (밑줄) 형식으로 작성할 것
- 섹션 사이에는 반드시 ━━━━━━━━━━ 구분선을 삽입할 것

1. __📋 오늘의 한 줄 요약__
   헤더 다음 줄에 반드시 >페르소나 어조의 한 문장을 인용 블록(blockquote)으로 작성

2. __🌏 글로벌 시장 동향__
   수집된 수치 데이터(지수값, 환율, 금리)는 아래처럼 코드 블록으로 묶을 것:
   ```
   나스닥: 18,234.56 (+2.35%)
   S&P500: 5,123.45 (+1.12%)
   환율: 1,320.50 원
   미 10년물: 4.25%
   ```
   이후 한국 시장 영향 분석은 일반 텍스트로 서술

3. __📰 핵심 뉴스 & 이슈__
   오늘 시장에 영향을 줄 상위 3~5개 뉴스를 한 줄씩 요약

4. __🔮 오늘의 증시 전망__
   분석 내용은 일반 텍스트로 서술하고, 최종 결론 한 줄만 ||스포일러||로 감싸서 클릭 유도

5. __🎯 대응 전략__
   한국·미국 시장 포지션 제안 (매수/매도/관망, 주목 섹터)

6. __⚠️ 리스크 요인__
   전망을 뒤집을 수 있는 핵심 변수 1~3가지

[Markdown 규칙 — 텔레그램 MarkdownV2 전용]
- 섹션 헤더 밑줄: __텍스트__
- 굵게: *텍스트* (별표 1개)
- 기울임: _텍스트_ (언더스코어 1개)
- 인용 블록: >텍스트 (줄 맨 앞에 > 붙이기)
- 스포일러: ||텍스트||
- 코드 블록: ```텍스트```
- 인라인 코드: `텍스트`
- 절대 사용 금지: **텍스트** (별표 2개), ### 헤더
- 특수문자 이스케이프는 하지 말 것 (후처리에서 자동 처리됨)
- 이모지는 페르소나 에너지에 맞는 빈도로 사용할 것
"""

    print("[Gemini] 리포트 생성 중...")
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    report = response.text
    report = sanitize_for_telegram_mdv2(report)
    print("[Gemini] 리포트 생성 완료:\n", report[:300], "...")

    # 텔레그램 전송
    print("[텔레그램] 게이지 이미지 전송 중...")
    tg_photo_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('fear_greed_gauge.png', gauge_image, 'image/png')}
    payload_photo = {'chat_id': CHAT_ID, 'caption': '📊 시장 심리: 공포 & 탐욕 지수 (8AM)'}
    tg_photo_response = requests.post(tg_photo_url, data=payload_photo, files=files)
    print(f"[텔레그램] 이미지 응답 코드: {tg_photo_response.status_code}")
    if not tg_photo_response.json().get("ok"):
        print(f"[텔레그램] 이미지 전송 실패: {tg_photo_response.text}")

    print("[텔레그램] 메시지 전송 중...")
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    tg_response = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": report, "parse_mode": "MarkdownV2"})
    print(f"[텔레그램] 응답 코드: {tg_response.status_code}")
    print(f"[텔레그램] 응답 본문: {tg_response.text}")

    # MarkdownV2 파싱 오류 발생 시 plain text로 재시도
    if not tg_response.json().get("ok") and tg_response.status_code == 400:
        print("[텔레그램] MarkdownV2 파싱 오류 감지 → plain text로 재시도")
        tg_response = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": report})
        print(f"[텔레그램] 재시도 응답 코드: {tg_response.status_code}")
        print(f"[텔레그램] 재시도 응답 본문: {tg_response.text}")

if __name__ == "__main__":
    summarize_and_send()