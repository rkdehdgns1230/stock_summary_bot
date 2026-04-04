import re
import requests
from . import config


def sanitize_for_telegram_mdv2(text: str) -> str:
    """
    MarkdownV2 sanitizer. 지원 포맷:
    *bold*, _italic_, __underline__, ~~strikethrough~~, ||spoiler||,
    `inline code`, ```code block```, >blockquote
    포맷팅 스팬은 내부 특수문자만 이스케이프하고 구분자는 보존.
    일반 텍스트는 MarkdownV2 특수문자를 전체 이스케이프.
    """
    PLAIN_ESCAPE_RE = re.compile(r'(?<!\\)([_*.\-+()~!=#>|{}\[\]])')
    INNER_ESCAPE_RE = re.compile(r'(?<!\\)([.\-+()!=#>{}\[\]])')

    protected = []

    def protect(content):
        idx = len(protected)
        protected.append(content)
        return f'\x00{idx}\x00'

    # 1. 코드 블록 우선 보호 (내부 이스케이프 없음)
    text = re.sub(r'```[\s\S]*?```', lambda m: protect(m.group()), text)

    # 2. 인라인 포맷팅 스팬 보호 (긴 구분자 우선 매칭)
    INLINE_RE = re.compile(
        r'__[^_\n]+?__'      # __underline__
        r'|\*\*[^*\n]+?\*\*' # **bold** → MarkdownV2 *bold*
        r'|_[^_\n]+?_'       # _italic_
        r'|~~[^\n]+?~~'      # ~~strikethrough~~
        r'|\|\|[^\n]+?\|\|'  # ||spoiler||
        r'|`[^`\n]+?`'       # `inline code`
    )

    def replace_inline(m):
        span = m.group()
        if span.startswith('__'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('__' + inner + '__')
        if span.startswith('~~'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('~~' + inner + '~~')
        if span.startswith('||'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('||' + inner + '||')
        if span.startswith('**'):
            # **bold** → MarkdownV2 *bold*
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[2:-2])
            return protect('*' + inner + '*')
        if span.startswith('_'):
            inner = INNER_ESCAPE_RE.sub(r'\\\1', span[1:-1])
            return protect('_' + inner + '_')
        return protect(span)  # `inline code`: 이스케이프 없이 보호

    text = INLINE_RE.sub(replace_inline, text)

    # 3. 일반 텍스트 이스케이프 (blockquote 줄은 > 접두어 보존)
    lines = text.split('\n')
    escaped = []
    for line in lines:
        if line.startswith('>'):
            escaped.append('>' + PLAIN_ESCAPE_RE.sub(r'\\\1', line[1:]))
        else:
            escaped.append(PLAIN_ESCAPE_RE.sub(r'\\\1', line))
    text = '\n'.join(escaped)

    # 4. 보호된 스팬 복원
    for i, p in enumerate(protected):
        text = text.replace(f'\x00{i}\x00', p)
    return text


_SECTION_DIVIDER = '\n━━━━━━━━━━\n'


def split_message(text: str, limit: int = 4096) -> list[str]:
    """━━━━━━━━━━ 섹션 구분선 기준으로 메시지를 분할.

    sections를 limit 이내로 그리디하게 묶어 반환한다.
    섹션 하나가 단독으로 limit을 초과하는 경우에도 그대로 청크로 emit한다.
    """
    sections = [s for s in text.split(_SECTION_DIVIDER) if s.strip()]
    if not sections:
        return [text]

    chunks = []
    current_parts: list[str] = []
    current_len = 0

    for section in sections:
        join_cost = len(_SECTION_DIVIDER) if current_parts else 0
        needed = join_cost + len(section)
        if current_parts and current_len + needed > limit:
            chunks.append(_SECTION_DIVIDER.join(current_parts))
            current_parts = [section]
            current_len = len(section)
        else:
            current_parts.append(section)
            current_len += needed

    if current_parts:
        chunks.append(_SECTION_DIVIDER.join(current_parts))

    return chunks


def send_gauge_image(gauge_image) -> None:
    """공포·탐욕 지수 게이지 이미지를 텔레그램으로 전송"""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"

    for chat_id in config.TELEGRAM_CHAT_IDS:
        gauge_image.seek(0)
        files = {'photo': ('fear_greed_gauge.png', gauge_image, 'image/png')}
        payload = {'chat_id': chat_id, 'caption': '📊 시장 심리: 공포 & 탐욕 지수 (8AM)'}
        print(f"[텔레그램] 게이지 이미지 전송 중... (chat_id={chat_id})")
        response = requests.post(url, data=payload, files=files)
        print(f"[텔레그램] 이미지 응답 코드: {response.status_code}")
        
        if not response.json().get("ok"):
            print(f"[텔레그램] 이미지 전송 실패: {response.text}")


def send_report(report: str) -> None:
    """리포트를 MarkdownV2로 전송. 4096자 초과 시 섹션 구분선 기준으로 분할 전송."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    chunks = split_message(report)
    print(f"[텔레그램] 메시지 {len(chunks)}개 청크로 전송 중...")

    for chat_id in config.TELEGRAM_CHAT_IDS:
        for i, chunk in enumerate(chunks, 1):
            print(f"[텔레그램] 청크 {i}/{len(chunks)} 전송 중... (chat_id={chat_id}, {len(chunk)}자)")
            response = requests.post(url, data={"chat_id": chat_id, "text": chunk, "parse_mode": "MarkdownV2"})
            print(f"[텔레그램] 응답 코드: {response.status_code}")
            print(f"[텔레그램] 응답 본문: {response.text}")

            if not response.json().get("ok") and response.status_code == 400:
                print(f"[텔레그램] MarkdownV2 파싱 오류 감지 → plain text로 재시도")
                response = requests.post(url, data={"chat_id": chat_id, "text": chunk})
                print(f"[텔레그램] 재시도 응답 코드: {response.status_code}")
                print(f"[텔레그램] 재시도 응답 본문: {response.text}")
