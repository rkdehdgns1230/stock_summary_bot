import os

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_IDS = [cid.strip() for cid in os.environ.get('TELEGRAM_CHAT_IDS', '').split(',') if cid.strip()]
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

RATING_KO = {
    "extreme fear": "극도의 공포",
    "fear": "공포",
    "neutral": "중립",
    "greed": "탐욕",
    "extreme greed": "극도의 탐욕",
}