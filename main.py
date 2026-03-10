import os
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# 1. 설정 (환경변수 사용)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)

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
    """코스피 200 야간 선물 수집 (인베스팅닷컴 우회)"""
    url = "https://kr.investing.com/indices/kospi-200-futures"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 인베스팅닷컴 구조상 데이터 속성 기반 추출 (구조 변경 시 수정 필요)
        price = soup.find("span", {"data-test": "instrument-price-last"}).text
        change = soup.find("span", {"data-test": "instrument-price-change-percent"}).text
        return f"코스피200 야간선물: {price} ({change})"
    except Exception:
        return "코스피200 야간선물: 정보 가져오기 실패"

def get_fmkorea_info():
    """에펨코리아 주식게시판 인기글 및 본문 수집"""
    url = "https://www.fmkorea.com/index.php?mid=stock&sort_index=pop&order_type=desc"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.select('.fm_best_widget li')[:15]  # 상위 15개

        results = []
        for post in posts:
            title_tag = post.select_one('h3.title a span.ellipsis-target')
            link_tag = post.select_one('h3.title a')
            if not title_tag or not link_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = link_tag['href']
            regdate_tag = post.select_one('span.regdate')
            regdate = regdate_tag.get_text(strip=True) if regdate_tag else ""

            # 본문 수집을 위한 상세 페이지 접속
            post_res = requests.get(f"https://www.fmkorea.com{link}", headers=headers)
            post_soup = BeautifulSoup(post_res.text, 'html.parser')
            content_tag = post_soup.select_one('.xe_content') or post_soup.select_one('article')
            content = content_tag.get_text(strip=True)[:300] if content_tag else "(본문 없음)"
            results.append(f"[{regdate}] 제목: {title}\n본문요약: {content}")
            time.sleep(1)  # 차단 방지

        return "\n---\n".join(results) if results else "인기글 없음"
    except Exception as e:
        return f"커뮤니티 정보 수집 실패: {e}"

def summarize_and_send():
    us_data = get_us_market()
    kospi_data = get_kospi_futures()
    fm_data = get_fmkorea_info()

    # Gemini 프롬프트 구성
    prompt = f"""
    너는 전문 주식 분석가이자 전략가야. 아래 데이터를 바탕으로 오늘 아침 한국 시장 투자 리포트를 작성해줘.
    
    1. 미국 시장 지표:
    {us_data}
    
    2. 국내 야간 선물:
    {kospi_data}
    
    3. 커뮤니티(에펨코리아) 여론:
    {fm_data}
    
    요구사항:
    - 텔레그램으로 읽기 편하게 이모지를 섞어서 요약해줘.
    - 커뮤니티 여론은 비속어를 정제하고 '개인 투자자들의 심리' 관점에서 분석해줘.
    - 오늘 한국 증시의 상승/하락 가능성을 전망해줘.
    """

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    report = response.text

    # 텔레그램 전송
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(tg_url, data={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"})

if __name__ == "__main__":
    summarize_and_send()