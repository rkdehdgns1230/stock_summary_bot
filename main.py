from datetime import datetime, timezone, timedelta

import ai_report
import chart
import config
import history_writer
import market_data
import telegram_sender


def summarize_and_send():
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    today = now_kst.strftime("%Y년 %m월 %d일")
    date_str = now_kst.strftime("%Y-%m-%d")

    score = market_data.get_fear_and_greed_score()
    print("[데이터 수집] 공포·탐욕 지수:\n", score)
    fng_stage = market_data.get_fng_description(score)
    gauge_image = chart.generate_fear_greed_gauge_image(score)

    us_data = market_data.fetch_us_market()
    print("[데이터 수집] 미국 시장 지표:\n", us_data)

    commodities_data = market_data.fetch_commodities_and_dollar()
    print("[데이터 수집] 원자재 및 달러 지수:\n", commodities_data)

    kospi_data = market_data.fetch_kospi_futures()
    print("[데이터 수집] 코스피:\n", kospi_data)

    kosdaq_data = market_data.fetch_kosdaq_index()
    print("[데이터 수집] 코스닥:\n", kosdaq_data)

    news_data = market_data.fetch_naver_finance_news()
    print("[데이터 수집] 네이버 금융 뉴스:\n", news_data[:300], "...")

    raw_report = ai_report.generate_report(today, score, fng_stage, us_data, commodities_data, kospi_data, kosdaq_data, news_data)

    if not config.IS_TEST_RUN:
        history_writer.save_daily_snapshot(date_str, score, fng_stage, us_data, commodities_data, kospi_data, kosdaq_data, news_data, raw_report)
        history_writer.upsert_fng_log(date_str, score, fng_stage)

    report = telegram_sender.sanitize_for_telegram_mdv2(raw_report)

    telegram_sender.send_gauge_image(gauge_image)
    telegram_sender.send_report(report)


if __name__ == "__main__":
    summarize_and_send()