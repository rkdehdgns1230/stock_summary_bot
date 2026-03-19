import importlib
import os
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest import mock


def _load_main_module():
    fake_history_writer = types.ModuleType('history_writer')
    fake_history_writer.save_daily_snapshot = mock.Mock()
    fake_history_writer.upsert_fng_log = mock.Mock()
    fake_history_writer.load_yesterday_snapshot = mock.Mock(return_value=None)

    fake_ai_report = types.ModuleType('ai_report')
    fake_ai_report.generate_report = mock.Mock()
    fake_ai_report.extract_structured_metadata = mock.Mock(return_value={})

    fake_chart = types.ModuleType('chart')
    fake_chart.generate_fear_greed_gauge_image = mock.Mock()

    fake_market_data = types.ModuleType('market_data')
    fake_market_data.get_fear_and_greed_score = mock.Mock()
    fake_market_data.get_fng_description = mock.Mock()
    fake_market_data.fetch_us_market = mock.Mock()
    fake_market_data.fetch_vix = mock.Mock()
    fake_market_data.fetch_commodities_and_dollar = mock.Mock()
    fake_market_data.fetch_kospi_futures = mock.Mock()
    fake_market_data.fetch_kosdaq_index = mock.Mock()
    fake_market_data.fetch_naver_finance_news = mock.Mock()

    fake_telegram_sender = types.ModuleType('telegram_sender')
    fake_telegram_sender.sanitize_for_telegram_mdv2 = mock.Mock()
    fake_telegram_sender.send_gauge_image = mock.Mock()
    fake_telegram_sender.send_report = mock.Mock()

    with mock.patch.dict(
        os.environ,
        {'GEMINI_API_KEY': 'test-gemini-key', 'TELEGRAM_CHAT_IDS': '123456789'},
        clear=False,
    ):
        with mock.patch.dict(
            sys.modules,
            {
                'ai_report': fake_ai_report,
                'chart': fake_chart,
                'history_writer': fake_history_writer,
                'market_data': fake_market_data,
                'telegram_sender': fake_telegram_sender,
            },
        ):
            if 'main' in sys.modules:
                return importlib.reload(sys.modules['main'])
            return importlib.import_module('main')


class SummarizeAndSendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = _load_main_module()

    def test_summarize_and_send_builds_report_from_collected_data(self):
        fixed_now = datetime(2026, 3, 14, 7, 36, 19, tzinfo=timezone.utc)
        gauge_image = object()

        mocked_datetime = mock.Mock()
        mocked_datetime.now.return_value = fixed_now

        with mock.patch.object(self.main, 'datetime', mocked_datetime), \
             mock.patch.object(self.main.market_data, 'get_fear_and_greed_score', return_value=65) as get_score, \
             mock.patch.object(self.main.market_data, 'get_fng_description', return_value='탐욕 (Greed)') as get_stage, \
             mock.patch.object(self.main.chart, 'generate_fear_greed_gauge_image', return_value=gauge_image) as make_gauge, \
             mock.patch.object(self.main.market_data, 'fetch_us_market', return_value='us data') as fetch_us, \
             mock.patch.object(self.main.market_data, 'fetch_vix', return_value='vix data') as fetch_vix, \
             mock.patch.object(self.main.market_data, 'fetch_commodities_and_dollar', return_value='commodities data') as fetch_commodities, \
             mock.patch.object(self.main.market_data, 'fetch_kospi_futures', return_value='kospi data') as fetch_kospi, \
             mock.patch.object(self.main.market_data, 'fetch_kosdaq_index', return_value='kosdaq data') as fetch_kosdaq, \
             mock.patch.object(self.main.market_data, 'fetch_naver_finance_news', return_value='news data') as fetch_news, \
             mock.patch.object(self.main.history_writer, 'load_yesterday_snapshot', return_value=None) as load_yesterday, \
             mock.patch.object(self.main.ai_report, 'generate_report', return_value='raw report') as generate_report, \
             mock.patch.object(self.main.ai_report, 'extract_structured_metadata', return_value={}) as extract_structured, \
             mock.patch.object(self.main.telegram_sender, 'sanitize_for_telegram_mdv2', return_value='sanitized report'), \
             mock.patch.object(self.main.telegram_sender, 'send_gauge_image'), \
             mock.patch.object(self.main.telegram_sender, 'send_report'):
            self.main.summarize_and_send()

        mocked_datetime.now.assert_called_once_with(self.main.timezone(self.main.timedelta(hours=9)))
        get_score.assert_called_once_with()
        get_stage.assert_called_once_with(65)
        make_gauge.assert_called_once_with(65)
        fetch_us.assert_called_once_with()
        fetch_vix.assert_called_once_with()
        fetch_commodities.assert_called_once_with()
        fetch_kospi.assert_called_once_with()
        fetch_kosdaq.assert_called_once_with()
        fetch_news.assert_called_once_with()
        load_yesterday.assert_called_once_with('2026-03-14')
        generate_report.assert_called_once_with(
            '2026년 03월 14일',
            65,
            '탐욕 (Greed)',
            'us data',
            'commodities data',
            'kospi data',
            'kosdaq data',
            'news data',
            vix_data='vix data',
            yesterday_report='',
        )
        extract_structured.assert_called_once_with('raw report')

    def test_summarize_and_send_sanitizes_report_before_sending(self):
        fixed_now = datetime(2026, 3, 14, 7, 36, 19, tzinfo=timezone.utc)
        gauge_image = object()

        mocked_datetime = mock.Mock()
        mocked_datetime.now.return_value = fixed_now

        call_order = mock.Mock()
        get_score = mock.Mock(return_value=42)
        get_stage = mock.Mock(return_value='공포 (Fear)')
        make_gauge = mock.Mock(return_value=gauge_image)
        fetch_us = mock.Mock(return_value='us data')
        fetch_vix = mock.Mock(return_value='vix data')
        fetch_commodities = mock.Mock(return_value='commodities data')
        fetch_kospi = mock.Mock(return_value='kospi data')
        fetch_kosdaq = mock.Mock(return_value='kosdaq data')
        fetch_news = mock.Mock(return_value='news data')
        load_yesterday = mock.Mock(return_value=None)
        generate_report = mock.Mock(return_value='raw report')
        extract_structured = mock.Mock(return_value={})
        sanitize_report = mock.Mock(return_value='sanitized report')
        send_gauge_image = mock.Mock()
        send_report = mock.Mock()

        call_order.attach_mock(get_score, 'get_score')
        call_order.attach_mock(get_stage, 'get_stage')
        call_order.attach_mock(make_gauge, 'make_gauge')
        call_order.attach_mock(fetch_us, 'fetch_us')
        call_order.attach_mock(fetch_vix, 'fetch_vix')
        call_order.attach_mock(fetch_commodities, 'fetch_commodities')
        call_order.attach_mock(fetch_kospi, 'fetch_kospi')
        call_order.attach_mock(fetch_kosdaq, 'fetch_kosdaq')
        call_order.attach_mock(fetch_news, 'fetch_news')
        call_order.attach_mock(load_yesterday, 'load_yesterday')
        call_order.attach_mock(generate_report, 'generate_report')
        call_order.attach_mock(extract_structured, 'extract_structured')
        call_order.attach_mock(sanitize_report, 'sanitize_report')
        call_order.attach_mock(send_gauge_image, 'send_gauge_image')
        call_order.attach_mock(send_report, 'send_report')

        with mock.patch.object(self.main, 'datetime', mocked_datetime), \
             mock.patch.object(self.main.market_data, 'get_fear_and_greed_score', get_score), \
             mock.patch.object(self.main.market_data, 'get_fng_description', get_stage), \
             mock.patch.object(self.main.chart, 'generate_fear_greed_gauge_image', make_gauge), \
             mock.patch.object(self.main.market_data, 'fetch_us_market', fetch_us), \
             mock.patch.object(self.main.market_data, 'fetch_vix', fetch_vix), \
             mock.patch.object(self.main.market_data, 'fetch_commodities_and_dollar', fetch_commodities), \
             mock.patch.object(self.main.market_data, 'fetch_kospi_futures', fetch_kospi), \
             mock.patch.object(self.main.market_data, 'fetch_kosdaq_index', fetch_kosdaq), \
             mock.patch.object(self.main.market_data, 'fetch_naver_finance_news', fetch_news), \
             mock.patch.object(self.main.history_writer, 'load_yesterday_snapshot', load_yesterday), \
             mock.patch.object(self.main.ai_report, 'generate_report', generate_report), \
             mock.patch.object(self.main.ai_report, 'extract_structured_metadata', extract_structured), \
             mock.patch.object(self.main.telegram_sender, 'sanitize_for_telegram_mdv2', sanitize_report), \
             mock.patch.object(self.main.telegram_sender, 'send_gauge_image', send_gauge_image), \
             mock.patch.object(self.main.telegram_sender, 'send_report', send_report):
            self.main.summarize_and_send()

        self.assertEqual(
            call_order.mock_calls,
            [
                mock.call.get_score(),
                mock.call.get_stage(42),
                mock.call.make_gauge(42),
                mock.call.fetch_us(),
                mock.call.fetch_vix(),
                mock.call.fetch_commodities(),
                mock.call.fetch_kospi(),
                mock.call.fetch_kosdaq(),
                mock.call.fetch_news(),
                mock.call.load_yesterday('2026-03-14'),
                mock.call.generate_report(
                    '2026년 03월 14일',
                    42,
                    '공포 (Fear)',
                    'us data',
                    'commodities data',
                    'kospi data',
                    'kosdaq data',
                    'news data',
                    vix_data='vix data',
                    yesterday_report='',
                ),
                mock.call.extract_structured('raw report'),
                mock.call.sanitize_report('raw report'),
                mock.call.send_gauge_image(gauge_image),
                mock.call.send_report('sanitized report'),
            ],
        )


if __name__ == '__main__':
    unittest.main()
