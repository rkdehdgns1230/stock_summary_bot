import ast
import os
import re


def _normalize_chat_id(chat_id: str | int) -> str:
    normalized = str(chat_id).strip().strip('"').strip("'")
    if not normalized:
        raise ValueError('TELEGRAM_CHAT_IDS contains an empty chat ID.')
    return normalized


def _parse_chat_ids(raw_chat_ids: str | None) -> list[str]:
    if raw_chat_ids is None:
        return []

    raw_chat_ids = raw_chat_ids.strip()
    if not raw_chat_ids:
        return []

    if raw_chat_ids.startswith('[') and raw_chat_ids.endswith(']'):
        parsed_chat_ids = ast.literal_eval(raw_chat_ids)
        if not isinstance(parsed_chat_ids, list):
            raise ValueError('TELEGRAM_CHAT_IDS must be a list or a comma-separated string.')
        return [_normalize_chat_id(chat_id) for chat_id in parsed_chat_ids]

    split_chat_ids = re.split(r'[\n,]+', raw_chat_ids)
    return [_normalize_chat_id(chat_id) for chat_id in split_chat_ids if chat_id.strip()]


def _get_raw_chat_ids() -> str | None:
    return os.environ.get('TELEGRAM_CHAT_IDS') or os.environ.get('TELEGRAM_CHAT_ID')


def _get_effective_chat_ids() -> list[str]:
    """실제 사용할 채팅 ID 목록 반환.

    TEST_TELEGRAM_CHAT_ID가 설정된 경우 해당 단일 ID만 반환하여
    E2E 스모크 테스트 시 전체 수신자에게 발송되는 것을 방지한다.
    """
    test_id = os.environ.get('TEST_TELEGRAM_CHAT_ID', '').strip()
    if test_id:
        return [_normalize_chat_id(test_id)]
    return _parse_chat_ids(_get_raw_chat_ids())


TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_IDS = _get_effective_chat_ids()
CHAT_IDS = TELEGRAM_CHAT_IDS
IS_TEST_RUN = bool(os.environ.get('TEST_TELEGRAM_CHAT_ID', '').strip())
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

RATING_KO = {
    "extreme fear": "극도의 공포",
    "fear": "공포",
    "neutral": "중립",
    "greed": "탐욕",
    "extreme greed": "극도의 탐욕",
}
