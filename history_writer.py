import csv
import json
from datetime import date, timedelta
from pathlib import Path

HISTORY_DIR = Path(__file__).parent / 'history'


def _ensure_dir() -> None:
    HISTORY_DIR.mkdir(exist_ok=True)


def save_daily_snapshot(date_str: str, fng_score: int, fng_stage: str,
                        us_data: str, commodities_data: str,
                        kospi_data: str, kosdaq_data: str,
                        news_data: str, report: str,
                        vix_data: str = '',
                        structured: dict | None = None) -> None:
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
            'vix': vix_data,
            'commodities': commodities_data,
            'kospi': kospi_data,
            'kosdaq': kosdaq_data,
        },
        'news': news_data,
        'report': report,
        'structured': structured or {},
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


def compute_forecast_record() -> dict:
    """히스토리 전체에서 AI 예측 전적(승/무/패) 집계.

    각 날짜 스냅샷의 structured.forecast_result 값을 읽어 집계한다.
    forecast_result가 'no_data'이거나 없는 날은 집계에서 제외한다.
    파일 읽기 오류는 건너뛰고 계속 집계한다.
    """
    hits, partials, misses = 0, 0, 0
    for json_file in sorted(HISTORY_DIR.glob('*.json')):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))
            result = data.get('structured', {}).get('forecast_result', 'no_data')
            if result == 'hit':
                hits += 1
            elif result == 'partial':
                partials += 1
            elif result == 'miss':
                misses += 1
        except Exception:
            continue
    return {'hits': hits, 'partials': partials, 'misses': misses}


def format_forecast_record(record: dict) -> str:
    """전적 dict를 Telegram MarkdownV2 호환 헤더 문자열로 변환.

    전적이 없으면(총 0회) 빈 문자열 반환.
    MarkdownV2 특수문자 ( ) 는 이스케이프 처리하여 직접 사용 가능.
    """
    total = record['hits'] + record['partials'] + record['misses']
    if total == 0:
        return ''
    return (
        f"📊 AI 예측 전적: "
        f"{record['hits']}승 {record['partials']}무 {record['misses']}패"
        f" \\(총 {total}회\\)"
    )
    """어제 날짜의 스냅샷 JSON을 로드하여 반환. 파일이 없으면 None 반환.

    Args:
        today_str: 오늘 날짜 문자열 (YYYY-MM-DD 형식)
    """
    try:
        today = date.fromisoformat(today_str)
        yesterday_str = (today - timedelta(days=1)).isoformat()
        path = HISTORY_DIR / f'{yesterday_str}.json'
        if not path.exists():
            print(f'[히스토리] 어제 스냅샷 없음: {path.name}')
            return None
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        print(f'[히스토리] 어제 스냅샷 로드 완료: {path.name}')
        return snapshot
    except Exception as e:
        print(f'[히스토리] 어제 스냅샷 로드 실패: {type(e).__name__}: {e}')
        return None
