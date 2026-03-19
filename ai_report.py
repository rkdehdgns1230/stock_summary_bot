from google import genai
from google.genai import types
import config

client = genai.Client(api_key=config.GEMINI_API_KEY)


def build_system_instruction() -> str:
    """모델의 고정 행동 원칙: 페르소나, 분석 사고 흐름, 출력 구조, 마크다운 규칙"""
    return """\
[페르소나 & 어조 — 가장 먼저, 가장 중요하게 읽을 것]
너는 '매일 아침 국장 모닝콜'을 해주는 친구다.
주식 고수지만 어렵게 말하지 않는다. 카톡 보내듯 편하고, 가끔은 재밌게.

글쓰기 5원칙:
1. 짧게 끊어라 — 한 문장에 하나의 메시지. 2줄 이상은 단락 분리.
2. "그래서 뭐?" 를 항상 붙여라 — 숫자·지표 뒤에 반드시 한국 증시 영향을 바로 연결.
3. 비유를 써라 — VIX, 금리 같은 추상 지표는 일상 언어로 번역해서 제시.
   (예: "VIX 30은 태풍 예보 뜬 날 아침 느낌", "금리가 오르면 성장주는 잠을 못 자")
4. 어려운 용어는 바로 풀어라 — 처음 나온 전문어는 괄호로 짧게 설명.
   (예: 장단기 금리차(장기·단기 채권 금리 차이, 경기 침체 신호로 읽힘))
5. 결론을 먼저, 근거는 그 다음 — 두 번째 문단 읽기 전에 핵심이 보여야 한다.

[절대 원칙]
- "지금 당장 사라/팔아라" 같은 직접적 매수·매도 권유 금지
- 섹터 흐름을 설명할 때 대표 종목 1~2개 언급은 허용.
  단, 반드시 "예시로", "대표적으로" 같은 표현과 함께 쓸 것.
  (예: "반도체 섹터 수급이 몰리고 있다. 대표적으로 삼성전자·SK하이닉스 흐름 주목.")
- 변동성 장세: '잃지 않는 투자' 우선, 분할 매수 원칙 강조
- 시장 과열: FOMO(남들 살 때 나도 사야 한다는 불안감) 경계

[분석 사고 흐름 — 이 순서로 내부 추론 후 리포트 작성]
Step 1.  나스닥·S&P500 방향·폭 → 오늘 국장 분위기 선행 파악
Step 2.  환율·미 10년물 금리 → 외국인 자금 이탈/유입 가능성
Step 3.  VIX 수준 해석 (20 미만=맑음 / 20~30=흐림 / 30+=폭풍주의보) → 공포 온도 체크
Step 4.  WTI·금·DXY → 글로벌 리스크온/오프 심리 판단
Step 5.  공포·탐욕 지수 → 시장 심리 과열·공포 구간 및 반전 가능성
Step 6.  뉴스 → 오늘 국장에 직타할 핵심 이슈 추출
Step 7.  1~6 종합 → 코스피·코스닥 방향·강도 결론
Step 8.  누락 데이터 → 나머지 지표로 최대한 추론·보완 (빈칸 금지)
Step 9.  [어제 데이터 제공 시] 어제 전망 vs 오늘 실제 비교·평가
Step 10. 필요 시 Google Search로 최신 이슈 보완 (네이버 뉴스 중복 최소화)

[출력 구조 — 섹션 순서 고정]
- 섹션 헤더: __이모지 헤더텍스트__ (언더스코어 2개)
- 섹션 사이: ━━━━━━━━━━ 구분선

1. __📊 어제 전망 vs 오늘 결과__  [어제 데이터가 제공된 경우에만, 없으면 섹션 2부터]
   어제 전망을 한 줄로 압축하고, 오늘 실제 흐름과 비교.
   판정: ✅ 적중 / ⚠️ 부분 적중 / ❌ 빗나감
   빗나갔다면 — 무엇 때문이었는지 짧게 짚는다. 솔직하게.

2. __☀️ 오늘의 한 줄 요약__
   헤더 다음 줄, 인용 블록으로 오늘 장의 분위기를 한 방에 정리.
   뉴스 헤드라인처럼 — 읽자마자 "아 오늘 이런 장이구나" 가 느껴져야 한다.
   >여기에 핵심 한 문장. 비유 환영, 이모지 환영.

3. __🌏 글로벌 시장 동향__
   수치 데이터는 코드 블록 안에 칼럼 정렬 테이블로:
   ```
   지표                현재값         등락
   ─────────────────────────────────────────
   나스닥            18,234.56     +2.35%
   S&P500             5,123.45     +1.12%
   코스피             2,635.00     -0.45%
   코스닥               845.00     +0.78%
   ─────────────────────────────────────────
   환율 (USD/KRW)     1,320.50         —
   미 10년물 금리         4.25%        —
   VIX                  18.45     -3.12%
   WTI 원유             78.50     -0.82%
   금 (Gold)         2,345.60     +0.34%
   달러 인덱스 (DXY)   104.23     -0.15%
   ```
   테이블 이후: 가장 눈에 띄는 수치 1~2개를 **굵게** 뽑고,
   "이게 국장에 어떤 의미냐?" 를 2~3문장으로 쉽게 풀어준다.
   전문가 설명 말고, 친구한테 설명하듯이.

4. __📰 핵심 뉴스 & 이슈__
   오늘 시장에 영향 줄 뉴스 3~5개를 불렛(-)으로.
   형식: _뉴스 제목 요약_ → **시장 영향 한 줄** 로 구성.
   (예: _연준 위원 매파 발언_ → **금리 인하 기대 꺾여, 성장주 압박 예상**)

5. __🔮 오늘의 증시 전망__
   2~3문단, 짧고 리듬감 있게.
   - 첫 문단: 오늘 코스피·코스닥 방향과 핵심 근거 (결론 먼저!)
   - 둘째 문단: 외인·기관 수급 흐름과 주목 섹터
   - **오늘 국장 관전 포인트:** (굵은 소제목)
     👀 이것만 봐도 오늘 장 감 잡힌다 — 불렛 2~3개
   - 마지막 한 줄: ||오늘의 최종 결론 — 클릭해서 확인||

6. __🎯 대응 전략__
   행동 가이드를 불렛으로, 짧고 명확하게:
   - 📌 포지션: 매수 확대 / 관망 / 비중 축소 중 하나 명시
   - 🔍 주목 섹터·테마
   - 🛡️ 리스크 관리 (분할 매수 기준, 손절 라인 등)

7. __⚠️ 리스크 요인__
   전망을 뒤집을 변수 1~3개를 불렛으로.
   형식: **변수** → 이렇게 되면 이런 시나리오
   무섭게 쓰지 말고, "이 정도는 알고 가자" 톤으로.

[Markdown 규칙 — 텔레그램 전용]
- 섹션 헤더 밑줄 : __텍스트__ (언더스코어 2개)
- 굵게           : **텍스트** (별표 2개)
- 기울임         : _텍스트_ (언더스코어 1개)
- 인용 블록      : >텍스트 (줄 맨 앞에 > 붙이기)
- 스포일러       : ||텍스트||
- 코드 블록      : ```텍스트```
- 인라인 코드    : `텍스트`
- 절대 사용 금지 : *텍스트* (별표 1개), ### 헤더
- 특수문자 이스케이프는 하지 말 것 (후처리에서 자동 처리됨)
- 이모지는 맥락에 맞게, 아끼되 눈에 띄게
"""


_DIRECTION_LABELS = {
    'bullish': '상승 (Bullish)',
    'bearish': '하락 (Bearish)',
    'neutral': '중립 (Neutral)',
}
_CONFIDENCE_LABELS = {'high': '높음', 'medium': '보통', 'low': '낮음'}


def _format_structured_summary(structured: dict) -> str:
    """어제 구조화 메타데이터를 AI가 해석하기 쉬운 텍스트 블록으로 변환"""
    direction = _DIRECTION_LABELS.get(structured.get('market_direction', ''), '알 수 없음')
    confidence = _CONFIDENCE_LABELS.get(structured.get('confidence', ''), '알 수 없음')
    key_risks = ', '.join(structured.get('key_risks', [])) or '없음'
    sector_focus = ', '.join(structured.get('sector_focus', [])) or '없음'
    fng_interp = structured.get('fng_interpretation', '알 수 없음')

    return f"""\
[어제 AI 전망 — 구조화 요약]
※ 아래 항목은 전날 AI가 추출한 메타데이터다. 오늘 실제 시장 흐름과 각 항목을 비교하여
   📊 어제 전망 vs 오늘 결과 섹션에서 예측의 적중 여부와 그 원인을 구체적으로 분석하라.

- 전망 방향  : {direction}
  → 오늘 코스피·코스닥 실제 방향과 일치했는가? 괴리가 있다면 원인을 설명하라.
- 확신도      : {confidence}
  → 실제 결과와 확신도가 얼마나 부합했는가?
- 핵심 리스크 : {key_risks}
  → 해당 리스크가 실제로 시장에 반영됐는가?
- 주목 섹터   : {sector_focus}
  → 해당 섹터의 실제 움직임은 어떠했는가?
- F&G 해석   : {fng_interp}
  → 오늘 F&G 지수 변화와 비교하라.\
"""


def _format_yesterday_section(yesterday_report: str,
                               yesterday_structured: dict | None) -> str:
    """어제 데이터 섹션 전체를 조립 (구조화 요약 + 리포트 전문)"""
    parts = []

    if yesterday_structured:
        parts.append(_format_structured_summary(yesterday_structured))

    if yesterday_report:
        parts.append(
            f"[어제 AI 전망 리포트 전문 — 구조화 요약의 근거 확인용]\n{yesterday_report}"
        )

    body = '\n\n'.join(parts)
    return (
        f"\n7. 어제 전망 데이터 (📊 섹션 작성에 활용):\n{body}\n"
        if body else ''
    )


def build_user_content(today: str,
                       us_data: str,
                       commodities_data: str,
                       kospi_data: str,
                       kosdaq_data: str,
                       fng_stage: str,
                       score: int,
                       news_data: str,
                       vix_data: str = '',
                       yesterday_report: str = '',
                       yesterday_structured: dict | None = None) -> str:
    """오늘의 시장 데이터와 리포트 작성 요청 메시지 생성"""
    vix_line = f'\n{vix_data}' if vix_data else ''
    yesterday_section = _format_yesterday_section(yesterday_report, yesterday_structured)

    return f"""\
오늘({today}) 아침 한국 주식시장 개장 전 투자자를 위한 모닝 브리핑 리포트를 작성해라.
아래 데이터는 자동 수집된 것으로 일부 항목이 누락되거나 "데이터 부족", "수집 실패" 상태일 수 있다.
누락·실패 항목은 절대 "데이터 없음"으로 건너뛰지 말고, 나머지 지표들 간의 상관관계와 시장 맥락을 활용해 합리적으로 추론하여 최선의 분석을 제공해야 한다.

[입력 데이터]
1. 미국 시장 지표 (전일 종가 기준):
{us_data}

2. 원자재 및 달러 인덱스 (전일 종가 기준):
{commodities_data}

3. 코스피 지수 (전일 종가 기준):
{kospi_data}

4. 코스닥 지수 (전일 종가 기준):
{kosdaq_data}

5. CNN 공포·탐욕 지수: {fng_stage} ({score}/100)
   - 0~24: 극도의 공포 / 25~44: 공포 / 45~55: 중립 / 56~75: 탐욕 / 76~100: 극도의 탐욕

6. 국내 증권 주요 뉴스 (네이버 금융):
{news_data}

6-1. VIX 변동성 지수 (전일 종가 기준):{vix_line}
   - 20 미만: 안정 / 20~30: 경계 / 30 이상: 고변동성·공포 구간
{yesterday_section}"""


def generate_report(today: str, score: int, fng_stage: str,
                    us_data: str, commodities_data: str,
                    kospi_data: str, kosdaq_data: str, news_data: str,
                    vix_data: str = '',
                    yesterday_report: str = '',
                    yesterday_structured: dict | None = None) -> str:
    """Gemini API를 호출하여 모닝 브리핑 리포트 텍스트 반환 (Google Search Grounding 활성화)"""
    system_instruction = build_system_instruction()
    user_content = build_user_content(today, us_data, commodities_data,
                                      kospi_data, kosdaq_data, fng_stage, score, news_data,
                                      vix_data=vix_data,
                                      yesterday_report=yesterday_report,
                                      yesterday_structured=yesterday_structured)
    print("[Gemini] 리포트 생성 중 (Google Search Grounding 활성화)...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
        contents=user_content,
    )
    print("[Gemini] 리포트 생성 완료")
    return response.text


_STRUCTURED_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        'market_direction': types.Schema(
            type=types.Type.STRING,
            enum=['bullish', 'bearish', 'neutral'],
            description='오늘 코스피/코스닥 전망 방향',
        ),
        'confidence': types.Schema(
            type=types.Type.STRING,
            enum=['high', 'medium', 'low'],
            description='전망 확신도',
        ),
        'key_risks': types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description='전망을 뒤집을 수 있는 핵심 리스크 (최대 3개)',
        ),
        'sector_focus': types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description='오늘 주목할 섹터 또는 업종 (최대 3개)',
        ),
        'fng_interpretation': types.Schema(
            type=types.Type.STRING,
            enum=['극도의 공포', '공포', '중립', '탐욕', '극도의 탐욕'],
            description='공포·탐욕 지수 해석',
        ),
        'forecast_result': types.Schema(
            type=types.Type.STRING,
            enum=['hit', 'partial', 'miss', 'no_data'],
            description=(
                '어제 전망의 적중 여부. '
                '"📊 어제 전망 vs 오늘 결과" 섹션이 있으면 판정 결과를 추출한다: '
                '✅ 적중 → hit, ⚠️ 부분 적중 → partial, ❌ 빗나감 → miss. '
                '해당 섹션이 없으면 → no_data.'
            ),
        ),
    },
    required=['market_direction', 'confidence', 'key_risks', 'sector_focus', 'fng_interpretation', 'forecast_result'],
)


def extract_structured_metadata(report_text: str) -> dict:
    """리포트 텍스트에서 구조화된 메타데이터 추출 (별도 Gemini 호출, response_schema 사용).

    Google Search Grounding과 response_schema는 동일 호출에서 사용 불가하므로
    리포트 생성 이후 별도 경량 호출로 구조화 추출한다.
    실패 시 빈 dict를 반환하여 메인 흐름을 중단하지 않는다.
    """
    prompt = f"""다음은 오늘의 한국 증시 모닝 브리핑 리포트다.
이 리포트를 읽고 아래 항목을 추출하라.

리포트에 "📊 어제 전망 vs 오늘 결과" 섹션이 있으면 그 판정을 forecast_result에 기록하라:
- ✅ 적중 → hit
- ⚠️ 부분 적중 → partial
- ❌ 빗나감 → miss
- 해당 섹션이 없으면 → no_data

리포트:
{report_text}
"""
    try:
        print("[Gemini] 구조화 메타데이터 추출 중...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=_STRUCTURED_SCHEMA,
            ),
            contents=prompt,
        )
        import json
        result = json.loads(response.text)
        print(f"[Gemini] 구조화 추출 완료: {result}")
        return result
    except Exception as e:
        print(f"[Gemini] 구조화 추출 실패: {type(e).__name__}: {e}")
        return {}
