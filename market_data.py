import requests
import yfinance as yf
from bs4 import BeautifulSoup
import config

_BODY_FETCH_COUNT = 5   # 본문을 수집할 상위 기사 수
_BODY_MAX_CHARS = 300   # 기사 본문 최대 수집 길이 (자)

def fetch_commodities_and_dollar() -> str:
    """원자재(WTI 원유, 금) 및 달러 인덱스(DXY) 수집"""
    tickers = {
        'WTI 원유': 'CL=F',
        '금(Gold)': 'GC=F',
        '달러 인덱스(DXY)': 'DX-Y.NYB',
    }
    results = []
    for name, ticker in tickers.items():
        try:
            data = yf.Ticker(ticker).history(period='2d')
            if len(data) >= 2:
                close = data['Close'].iloc[-1]
                prev_close = data['Close'].iloc[-2]
                change_pct = ((close - prev_close) / prev_close) * 100
                results.append(f'{name}: {close:.2f} ({change_pct:+.2f}%)')
            else:
                results.append(f'{name}: 데이터 부족 (rows={len(data)})')
        except Exception as e:
            results.append(f'{name}: 수집 실패 ({type(e).__name__})')
    return '\n'.join(results)


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


def _fetch_article_body(article_url: str, headers: dict) -> str:
    """네이버 금융 뉴스 기사 본문 수집 (실패 시 빈 문자열 반환)

    네이버 금융 뉴스 read 페이지는 기사 본문을 iframe으로 제공하므로,
    iframe src를 추출한 뒤 해당 페이지에서 본문 셀렉터를 순서대로 시도한다.
    """
    try:
        res = requests.get(article_url, headers=headers, timeout=5)
        res.encoding = 'euc-kr'
        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, 'html.parser')
        iframe = soup.find('iframe', id='newsFrame')
        if not iframe or not iframe.get('src'):
            return ""

        iframe_src = iframe['src']
        if not iframe_src.startswith('http'):
            iframe_src = 'https://finance.naver.com' + iframe_src

        iframe_res = requests.get(iframe_src, headers=headers, timeout=5)
        iframe_res.encoding = 'utf-8'
        if iframe_res.status_code != 200:
            return ""

        iframe_soup = BeautifulSoup(iframe_res.text, 'html.parser')
        for selector in ['#dic_area', '#articleBodyContents', '.newsct_article', '#articeBody']:
            content = iframe_soup.select_one(selector)
            if content:
                text = ' '.join(content.get_text(strip=True).split())
                return text[:_BODY_MAX_CHARS]
    except Exception:
        pass
    return ""


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

            if i < _BODY_FETCH_COUNT:
                href = article.get('href', '')
                article_url = ('https://finance.naver.com' + href) if href.startswith('/') else href
                body = _fetch_article_body(article_url, headers) if article_url else ''
                if body:
                    print(f"[네이버금융] 기사 #{i+1} 본문 수집 완료 ({len(body)}자)")
                    results.append(f"- {title}\n  본문: {body}")
                else:
                    print(f"[네이버금융] 기사 #{i+1} 본문 수집 실패")
                    results.append(f"- {title}")
            else:
                results.append(f"- {title}")

        print(f"[네이버금융] 최종 수집된 기사 수: {len(results)}")
        return "\n".join(results)
    except Exception as e:
        print(f"[네이버금융] 예외 발생: {type(e).__name__}: {e}")
        return f"뉴스 수집 실패: {e}"