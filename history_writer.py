import csv
import json
from pathlib import Path

HISTORY_DIR = Path(__file__).parent / 'history'


def _ensure_dir() -> None:
    HISTORY_DIR.mkdir(exist_ok=True)


def save_daily_snapshot(date_str: str, fng_score: int, fng_stage: str,
                        us_data: str, commodities_data: str,
                        kospi_data: str, kosdaq_data: str,
                        news_data: str, report: str) -> None:
    """날짜별 JSON 스냅샷 저장.

    같은 날짜에 여러 번 실행되더라도 항상 최신 값으로 덮어씀.
    스모크 테스트(TEST_TELEGRAM_CHAT_ID 설정)에서는 main.py가 이 함수를 호출하지 않음.
    """
    _ensure_dir()
    snapshot = {
        'date': date_str,
        'fng_score': fng_score,
        'fng_stage': fng_stage,
        'market': {
            'us': us_data,
            'commodities': commodities_data,
            'kospi': kospi_data,
            'kosdaq': kosdaq_data,
        },
        'news': news_data,
        'report': report,
    }
    path = HISTORY_DIR / f'{date_str}.json'
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[히스토리] 스냅샷 저장: {path.name}')


def upsert_fng_log(date_str: str, fng_score: int, fng_stage: str) -> None:
    """공포탐욕 지수 CSV 누적 로그 업서트.

    해당 날짜 행이 이미 있으면 갱신, 없으면 추가.
    """
    _ensure_dir()
    log_path = HISTORY_DIR / 'fng_log.csv'
    rows: list[dict] = []
    updated = False

    if log_path.exists():
        with open(log_path, encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                if row['date'] == date_str:
                    rows.append({'date': date_str, 'score': str(fng_score), 'stage': fng_stage})
                    updated = True
                else:
                    rows.append(row)

    if not updated:
        rows.append({'date': date_str, 'score': str(fng_score), 'stage': fng_stage})

    with open(log_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'score', 'stage'])
        writer.writeheader()
        writer.writerows(rows)

    action = '갱신' if updated else '추가'
    print(f'[히스토리] FNG 로그 {action}: {date_str} (score={fng_score}, stage={fng_stage})')
