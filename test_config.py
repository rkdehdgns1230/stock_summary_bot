import os
import unittest
from unittest import mock

import config


class ParseChatIdsTest(unittest.TestCase):
    def test_comma_separated_chat_ids(self):
        self.assertEqual(
            config._parse_chat_ids('123456789, 987654321'),
            ['123456789', '987654321'],
        )

    def test_list_style_chat_ids(self):
        self.assertEqual(
            config._parse_chat_ids('["123456789", "987654321"]'),
            ['123456789', '987654321'],
        )

    def test_empty_entries_raise_value_error_for_list_style_input(self):
        with self.assertRaises(ValueError):
            config._parse_chat_ids('["123456789", ""]')

    def test_module_exposes_telegram_chat_ids_from_environment(self):
        with mock.patch.dict(os.environ, {'TELEGRAM_CHAT_IDS': '["123456789", "987654321"]'}, clear=False):
            with mock.patch('config.os.environ', os.environ):
                self.assertEqual(config._parse_chat_ids(os.environ.get('TELEGRAM_CHAT_IDS')), ['123456789', '987654321'])


if __name__ == '__main__':
    unittest.main()
