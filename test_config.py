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

    def test_newline_separated_chat_ids(self):
        self.assertEqual(
            config._parse_chat_ids('123456789\n987654321'),
            ['123456789', '987654321'],
        )

    def test_empty_entries_raise_value_error_for_list_style_input(self):
        with self.assertRaises(ValueError):
            config._parse_chat_ids('["123456789", ""]')

    def test_get_raw_chat_ids_prefers_plural_variable(self):
        with mock.patch.dict(
            os.environ,
            {'TELEGRAM_CHAT_IDS': '123456789,987654321', 'TELEGRAM_CHAT_ID': '111111111'},
            clear=False,
        ):
            self.assertEqual(config._get_raw_chat_ids(), '123456789,987654321')

    def test_get_raw_chat_ids_falls_back_to_legacy_variable(self):
        with mock.patch.dict(os.environ, {'TELEGRAM_CHAT_IDS': '', 'TELEGRAM_CHAT_ID': '123456789'}, clear=False):
            self.assertEqual(config._get_raw_chat_ids(), '123456789')


if __name__ == '__main__':
    unittest.main()
