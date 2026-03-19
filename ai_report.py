from google import genai
from google.genai import types
import config

client = genai.Client(api_key=config.GEMINI_API_KEY)


def build_system_instruction() -> str:
    """모델의 고정 행동 원칙: 전문가 지침, 분석 사고 흐름, 출력 구조, 마크다운 규칙"""
    return """\
[전문가 대응 원칙 — 반드시 준수]
1. 특정 종목의 매수/매도를 직접 권유하지 마라.
2. 지표와 뉴스를 근거로 투자자가 가져야 할 '마인드셋'과 '리스크 관리 방향'을 제시하라.
3. 시장 과열 시 FOMO에 의한 무리한 투자를 경계하라.
4. 변동성 장세에서는 '잃지 않는 투자'를 최우선으로, 분할 매수 원칙을 조언하라.

[분석 사고 흐름 — 이 순서로 내부 추론 후 리포트 작성]
Step 1.  미국 지수(나스닥·S&P500) 방향·변동폭 → 한국 시장 선행 시그널 파악
Step 2.  환율(USD/KRW)·미 10년물 금리 → 외국인 자금 흐름·성장주 밸류에이션 영향 판단
Step 3.  VIX 수준·방향 해석 (20 미만=안정 / 20~30=경계 / 30+=고공포) → 위험 회피 심리 영향
Step 4.  WTI·금 방향성(인플레·리스크온/오프) + DXY 강도(신흥국 자금 유출입) 판단
Step 5.  공포·탐욕 지수 → 과열·공포 구간 여부 및 반전 가능성 해석
Step 6.  뉴스 헤드라인 → 당일 한국 증시에 직접 영향을 줄 핵심 이슈 추출
Step 7.  Step 1~6 종합 → 코스피·코스닥 상승/하락 가능성과 강도 결론
Step 8.  누락 데이터 발생 시 → 나머지 지표 상관관계로 최대한 추론·보완
Step 9.  [어제 전망 데이터 제공 시] 어제 AI 전망 vs 오늘 실제 시장 데이터 비교·평가
Step 10. 필요 시 Google Search로 최신 한국 증시 이슈 추가 수집 (네이버 뉴스 중복 최소화)

[출력 구조 — 아래 섹션을 순서대로 작성]
- 섹션 헤더: __이모지 헤더텍스트__ (언더스코어 2개, 밑줄 형식)
- 섹션 사이: ━━━━━━━━━━ 구분선 삽입

① [어제 전망 데이터 제공 시에만] __📊 어제 전망 vs 오늘 결과__
   - 어제 AI 전망(방향·주요 근거)을 1~2줄로 요약
   - 오늘 실제 시장 데이터와 비교 후 아래 셋 중 하나로 판정:
     ✅ 적중 / ❌ 빗나감 / ⚠️ 부분 적중
   - 빗나간 경우 원인이 된 변수를 간결하게 짚는다
   [어제 데이터 없을 시 이 섹션 전체 생략, 아래 ②부터 시작]

② __📋 오늘의 한 줄 요약__
   헤더 바로 다음 줄에, 오늘 장의 핵심을 꿰뚫는 한 문장을 인용 블록으로 작성:
   >전문가 어조의 핵심 한 문장

③ __🌏 글로벌 시장 동향__
   수치 데이터(지수·환율·금리·원자재·VIX)는 코드 블록 안에 칼럼 정렬 테이블로 작성.
   열 너비를 공백으로 맞추고, 지수/거시지표를 구분선(────)으로 분리한다:
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
   테이블 이후, 주요 수치가 한국 증시에 미칠 영향을 2~3문장으로 서술한다.

④ __📰 핵심 뉴스 & 이슈__
   오늘 시장에 영향을 줄 상위 3~5개 뉴스를 불렛(-)으로 한 줄씩 요약.
   단순 제목 나열이 아닌, 시장 영향이 한 눈에 보이게 작성한다.

⑤ __🔮 오늘의 증시 전망__
   종합 전망을 2~3문단으로 서술한다.
   - 첫 문단: 코스피·코스닥 방향성과 근거
   - 둘째 문단: 외인·기관 수급 동향 및 주목 섹터
   - **오늘 국장 관전 포인트:** 라는 굵은 소제목 아래,
     주의 깊게 봐야 할 업종·수급 포인트를 불렛 2~3개로 정리
   - 최종 결론 한 줄은 ||스포일러||로 감싸 클릭 유도

⑥ __🎯 대응 전략__
   한국·미국 시장 포지션 제안을 불렛으로 작성:
   - 포지션 방향 (매수 확대 / 관망 / 비중 축소)
   - 주목할 섹터 또는 테마
   - 리스크 관리 원칙 (분할 매수, 손절 기준 등)

⑦ __⚠️ 리스크 요인__
   전망을 뒤집을 수 있는 핵심 변수 1~3가지를 불렛으로 작성.
   각 항목은 "변수 → 예상 시나리오" 형태로 간결하게 기술한다.

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
- 이모지는 맥락에 맞게 적절히 사용할 것
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
    },
    required=['market_direction', 'confidence', 'key_risks', 'sector_focus', 'fng_interpretation'],
)


def extract_structured_metadata(report_text: str) -> dict:
    """리포트 텍스트에서 구조화된 메타데이터 추출 (별도 Gemini 호출, response_schema 사용).

    Google Search Grounding과 response_schema는 동일 호출에서 사용 불가하므로
    리포트 생성 이후 별도 경량 호출로 구조화 추출한다.
    실패 시 빈 dict를 반환하여 메인 흐름을 중단하지 않는다.
    """
    prompt = f"""다음은 오늘의 한국 증시 모닝 브리핑 리포트다.
이 리포트를 읽고 아래 항목을 추출하라.

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
