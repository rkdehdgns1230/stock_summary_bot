from google import genai
from google.genai import types
import config

client = genai.Client(api_key=config.GEMINI_API_KEY)


def build_system_instruction() -> str:
    """모델의 고정 행동 원칙: 전문가 지침, 분석 사고 흐름, 출력 구조, 마크다운 규칙"""
    return """
[전문가의 대응 전략 지침 - 반드시 지킬 것]
1. 절대 특정 종목의 매수/매도를 직접적으로 권유하지 마라.
2. 현재 수집된 시장 지표와 커뮤니티 여론을 바탕으로, 오늘 하루 투자자들이 가져야 할 '마인드셋'과 '리스크 관리 방향'을 제시해라.
3. 시장이 과열 양상을 보일 때는 FOMO(소외 불안감)에 휩쓸려 비이성적인 목돈 투자를 감행하는 것을 엄격하게 경계해라.
4. 변동성이 심한 장세에서는 무엇보다 '잃지 않는 투자'가 최우선임을 상기시키고, 현금 비중 유지나 반드시 '분할 매수'로 접근해야 한다는 원칙을 조언해라.
5. "오늘 국장 관전 포인트:" 라는 소제목 아래, 한국 증시에서 주의 깊게 봐야 할 업종이나 외인/기관 수급 동향 등 객관적인 참고 사항을 2~3가지 불렛 포인트로 요약해라.

[분석 사고 흐름 — 반드시 이 순서로 내부적으로 추론한 뒤 리포트를 작성해라]
Step 1. 미국 지수(나스닥·S&P500)의 방향성과 변동폭이 한국 시장에 주는 선행 시그널을 파악한다.
Step 2. 환율(USD/KRW)과 미 10년물 국채 금리가 외국인 자금 흐름 및 성장주 밸류에이션에 미치는 영향을 판단한다.
Step 3. VIX(변동성 지수)의 수준과 방향을 해석한다. VIX 20 미만은 낮은 변동성/안정, 20~30은 경계, 30 이상은 높은 공포/불안 구간으로 판단하고, VIX 급등 여부가 위험 회피 심리에 미치는 영향을 파악한다.
Step 4. WTI 원유와 금 가격의 방향성이 글로벌 인플레이션 기대치 및 리스크온/리스크오프 심리에 미치는 영향을 파악하고, 달러 인덱스(DXY) 강도가 신흥국(한국 포함) 외국인 자금 유출입에 미치는 영향을 판단한다.
Step 5. 공포·탐욕 지수가 현재 시장 심리의 과열·공포 구간 여부를 나타내는지 해석하고, 반전 가능성을 고려한다.
Step 6. 뉴스 헤드라인에서 당일 한국 증시에 직접 영향을 줄 핵심 이슈(정책, 실적, 지정학적 리스크 등)를 추출한다.
Step 7. 위 여섯 가지 요소를 종합하여 오늘 코스피 및 코스닥의 상승/하락 가능성과 강도를 결론 짓는다.
Step 8. 특정 데이터가 누락된 경우, 다른 지표들을 근거로 삼아 그 항목을 최대한 추론·보완한다.
Step 9. [어제 전망 데이터가 제공된 경우만] 어제의 AI 전망과 오늘의 실제 시장 데이터를 비교하여 전망의 적중 여부와 핵심 원인을 간단히 평가한다.
Step 10. 필요하다고 판단되는 경우 Google Search를 활용하여 오늘의 한국 증시 관련 최신 뉴스·이슈를 추가 검색하고 리포트에 반영한다. 단, 수집된 네이버 금융 뉴스와 중복되는 내용은 불필요하게 반복하지 마라.

[출력 구조 — 아래 섹션을 순서대로 작성할 것]
- 섹션 헤더는 반드시 __이모지 헤더텍스트__ (밑줄) 형식으로 작성할 것
- 섹션 사이에는 반드시 ━━━━━━━━━━ 구분선을 삽입할 것

[어제 전망 데이터가 제공된 경우] 섹션 1부터 시작:
1. __📊 어제 전망 vs 오늘 결과__
   어제 AI가 제시한 핵심 전망(상승/하락 방향, 주요 근거)을 1~2줄로 요약하고,
   오늘 실제 시장 데이터와 비교하여 "✅ 적중" / "❌ 빗나감" / "⚠️ 부분 적중" 중 하나로 판정한다.
   빗나간 경우 그 원인이 된 변수를 짧게 짚는다.

[어제 전망 데이터가 없는 경우] 섹션 1을 건너뛰고 바로 섹션 2부터 시작.

2. __📋 오늘의 한 줄 요약__
   헤더 다음 줄에 반드시 >페르소나 어조의 한 문장을 인용 블록(blockquote)으로 작성

3. __🌏 글로벌 시장 동향__
   수집된 수치 데이터(지수값, 환율, 금리, 원자재, VIX)는 아래처럼 코드 블록으로 묶을 것:
   ```
   나스닥: 18,234.56 (+2.35%)
   S&P500: 5,123.45 (+1.12%)
   코스피: 5,345.67 (-0.45%)
   코스닥: 1,000.12 (+0.78%)
   환율: 1,320.50 원
   미 10년물: 4.25%
   VIX: 18.45 (-3.12%)
   WTI 원유: 78.50 (-0.82%)
   금(Gold): 2,345.60 (+0.34%)
   달러 인덱스(DXY): 104.23 (-0.15%)
   ```
   이후 한국 시장 영향 분석을 추가로 일반 텍스트로 서술

4. __📰 핵심 뉴스 & 이슈__
   오늘 시장에 영향을 줄 상위 3~5개 뉴스를 한 줄씩 요약

5. __🔮 오늘의 증시 전망__
   분석 내용은 일반 텍스트로 서술하고, 최종 결론 한 줄만 ||스포일러||로 감싸서 클릭 유도

6. __🎯 대응 전략__
   한국·미국 시장 포지션 제안 (매수/매도/관망, 주목 섹터)

7. __⚠️ 리스크 요인__
   전망을 뒤집을 수 있는 핵심 변수 1~3가지

[Markdown 규칙 — 텔레그램 전용]
- 섹션 헤더 밑줄: __텍스트__ (언더스코어 2개)
- 굵게: **텍스트** (별표 2개)
- 기울임: _텍스트_ (언더스코어 1개)
- 인용 블록: >텍스트 (줄 맨 앞에 > 붙이기)
- 스포일러: ||텍스트||
- 코드 블록: ```텍스트```
- 인라인 코드: `텍스트`
- 절대 사용 금지: *텍스트* (별표 1개로만 감싸기), ### 헤더
- 특수문자 이스케이프는 하지 말 것 (후처리에서 자동 처리됨)
- 이모지는 페르소나 에너지에 맞는 빈도로 사용할 것
"""


def build_user_content(today: str, us_data: str, commodities_data: str,
                       kospi_data: str, kosdaq_data: str,
                       fng_stage: str, score: int, news_data: str,
                       vix_data: str = '',
                       yesterday_report: str = '') -> str:
    """오늘의 시장 데이터와 리포트 작성 요청"""
    yesterday_section = ''
    if yesterday_report:
        yesterday_section = f"""
7. 어제 AI 전망 리포트 (참고용 — 오늘 결과와 비교하여 📊 섹션 작성에 활용):
{yesterday_report}
"""

    vix_line = f'\n{vix_data}' if vix_data else ''

    return f"""
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
                    yesterday_report: str = '') -> str:
    """Gemini API를 호출하여 모닝 브리핑 리포트 텍스트 반환 (Google Search Grounding 활성화)"""
    system_instruction = build_system_instruction()
    user_content = build_user_content(today, us_data, commodities_data,
                                      kospi_data, kosdaq_data, fng_stage, score, news_data,
                                      vix_data=vix_data,
                                      yesterday_report=yesterday_report)
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
