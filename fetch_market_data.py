import yfinance as yf

def get_us_market():
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

print(get_us_market())
