import os
from datetime import datetime, timezone, timedelta
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from google import genai
import time

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

def summarize_and_send():
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y년 %m월 %d일")

    us_data = get_us_market()
    print("[데이터 수집] 미국 시장 지표:\n", us_data)

    kospi_data = get_kospi_futures()
    print("[데이터 수집] 코스피200 야간선물:\n", kospi_data)

    news_data = get_naver_finance_news()
    print("[데이터 수집] 네이버 금융 뉴스:\n", news_data[:300], "...")

    # Gemini 프롬프트 구성
    prompt = f"""
    너는 전문 주식 분석가이자 전략가야. 아래 데이터를 바탕으로 {today} 아침 한국 시장 투자 리포트를 작성해줘.
    
    1. 미국 시장 지표:
    {us_data}
    
    2. 코스피200 지수 (전일 종가 기준):
    {kospi_data}
    
    3. 국내 증권 주요 뉴스 (네이버 금융):
    {news_data}
    
    요구사항:
    - 텔레그램으로 읽기 편하게 이모지를 섞어서 요약해줘.
    - 커뮤니티 여론 대신 국내 증권 뉴스 헤드라인을 바탕으로 시장 분위기를 분석해줘.
    - 오늘 한국 증시의 상승/하락 가능성을 전망해줘.
    - 텔레그램 Markdown 형식으로 작성해줘. 아래 규칙을 반드시 지켜줘:
      * 굵게 표시는 *텍스트* (별표 1개)
      * 기울임 표시는 _텍스트_ (언더스코어 1개)
      * 코드 표시는 `텍스트`
      * **텍스트** (별표 2개), ~~취소선~~, # 헤더 등은 사용하지 마줘.
      * 열리는 기호와 닫히는 기호가 반드시 짝을 이뤄야 해.
    """

    print("[Gemini] 리포트 생성 중...")
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    report = response.text
    print("[Gemini] 리포트 생성 완료:\n", report[:300], "...")

    # 텔레그램 전송
    print("[텔레그램] 메시지 전송 중...")
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    tg_response = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})
    print(f"[텔레그램] 응답 코드: {tg_response.status_code}")
    print(f"[텔레그램] 응답 본문: {tg_response.text}")

    # Markdown 파싱 오류 발생 시 plain text로 재시도
    if not tg_response.json().get("ok") and tg_response.status_code == 400:
        print("[텔레그램] Markdown 파싱 오류 감지 → plain text로 재시도")
        tg_response = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": report})
        print(f"[텔레그램] 재시도 응답 코드: {tg_response.status_code}")
        print(f"[텔레그램] 재시도 응답 본문: {tg_response.text}")

if __name__ == "__main__":
    summarize_and_send()