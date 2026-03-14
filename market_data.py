import requests
import yfinance as yf
from bs4 import BeautifulSoup
import config

def fetch_us_market():
    tickers = {
        '나스닥': '^IXIC',
        'S&P500': '^GSPC',
        '환율(USD/KRW)': 'KRW=X',
        '미10년물국채': '^TNX'
    }
    market_results = []
    for name, ticker in tickers.items():
        data = yf.Ticker(ticker).history(period='2d')
        if len(data) >= 2:
            close = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            change_pct = ((close - prev_close) / prev_close) * 100
            market_results.append(f'{name}: {close:.2f} ({change_pct:+.2f}%)')
        else:
            market_results.append(f'{name}: 데이터 부족 (rows={len(data)})')
    return '\n'.join(market_results)


def fetch_kospi_futures():
    """코스피 지수 수집 (yfinance)"""
    try:
        print("[코스피] yfinance로 데이터 요청 중...")
        data = yf.Ticker("^KS11").history(period="2d")
        print(f"[코스피] 수신된 데이터 행 수: {len(data)}")

        if len(data) < 2:
            print(f"[코스피] 데이터 부족: {data}")
            return "코스피: 데이터 부족"

        close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        change_pct = ((close - prev_close) / prev_close) * 100
        result = f"코스피: {close:.2f} ({change_pct:+.2f}%)"
        print(f"[코스피] 수집 완료: {result}")
        return result
    except Exception as e:
        print(f"[코스피] 예외 발생: {type(e).__name__}: {e}")
        return "코스피: 정보 가져오기 실패"

def fetch_kosdaq_index():
    """코스닥 지수 수집 (yfinance)"""
    try:
        print("[코스닥] yfinance로 데이터 요청 중...")
        data = yf.Ticker("^KQ11").history(period="2d")
        print(f"[코스닥] 수신된 데이터 행 수: {len(data)}")

        if len(data) < 2:
            print(f"[코스닥] 데이터 부족: {data}")
            return "코스닥: 데이터 부족"

        close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        change_pct = ((close - prev_close) / prev_close) * 100
        result = f"코스닥: {close:.2f} ({change_pct:+.2f}%)"
        print(f"[코스닥] 수집 완료: {result}")
        return result
    except Exception as e:
        print(f"[코스닥] 예외 발생: {type(e).__name__}: {e}")
        return "코스닥: 정보 가져오기 실패"


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
        rating_ko = config.RATING_KO.get(rating_en, rating_en)
        prev_close = round(data["previous_close"])
        result = f"공포·탐욕 지수: {score}/100 ({rating_ko}) | 전일: {prev_close}"
        print(f"[공포와탐욕] 수집 완료: {result}")
        return score
    except Exception as e:
        print(f"[공포와탐욕] 예외 발생: {type(e).__name__}: {e}")
        return -1

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


def fetch_naver_finance_news() -> str:
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