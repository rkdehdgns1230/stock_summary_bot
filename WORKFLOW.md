# 개발 워크플로우 가이드

> **Copilot 세션 참조용 문서입니다.**  
> 이 프로젝트에서 작업할 때 따라야 할 개발·테스트·배포 절차를 정리합니다.  
> 아키텍처·환경변수·디버깅 순서는 `CONTEXT.md`를 함께 참조하세요.

---

## 1. 브랜치 전략

| 브랜치 | 용도 |
|--------|------|
| `main` | 프로덕션 브랜치. 직접 push는 지양하고, 작업 완료 후 PR 또는 검토된 커밋만 merge |
| `feature/*` | 기능 추가·개선 |
| `fix/*` | 버그 수정 |
| `chore/*` | 의존성 업데이트, CI 설정, 문서 변경 등 코드 외 작업 |

---

## 2. 로컬 개발 절차

### 2-1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2-2. 환경변수 설정 (로컬)

```powershell
# Windows PowerShell
$env:TELEGRAM_TOKEN="your_token"
$env:TELEGRAM_CHAT_IDS='["your_chat_id"]'
$env:GEMINI_API_KEY="your_gemini_api_key"
```

### 2-3. 스모크 테스트 (단일 수신자, 실 API 호출)

```bash
TEST_TELEGRAM_CHAT_ID=your_chat_id python main.py
```

`TEST_TELEGRAM_CHAT_ID`가 설정되면 `TELEGRAM_CHAT_IDS`의 전체 수신자 대신 해당 ID에게만 발송됩니다.  
→ 히스토리 저장(`history/`) 도 **스킵**됩니다.

---

## 3. 테스트

### 단위 테스트 실행

```bash
python -m unittest -q
```

- 테스트 파일: `test_config.py`, `test_main.py`
- 프레임워크: `unittest` + `unittest.mock`
- **새 기능·파싱 로직 변경 시 반드시 대응하는 단위 테스트를 추가**합니다.

### 커밋 전 체크리스트

- [ ] `python -m unittest -q` 통과
- [ ] `git diff`로 의도한 파일만 변경됐는지 확인
- [ ] 환경변수 이름이 코드·워크플로우·README·CONTEXT.md에서 일치하는지 확인
- [ ] 변경 내용을 `CHANGELOG.md`에 기록

---

## 4. GitHub Actions 워크플로우

### 4-1. 프로덕션 스케줄 실행 (`daily_report.yml`)

- **트리거**: 매일 UTC 23:00 (KST 08:00) 자동 실행 + 수동 실행(`workflow_dispatch`)
- **필수 Secrets**:

  | Secret 이름 | 설명 |
  |-------------|------|
  | `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
  | `TELEGRAM_CHAT_IDS` | 수신자 채팅 ID (JSON 배열 형식 권장: `["id1","id2"]`) |
  | `GEMINI_API_KEY` | Gemini API 키 |

- **권한 설정**: `build` job에 `permissions: contents: write` 필수  
  (히스토리 파일 자동 커밋·푸시를 위해 필요)

### 4-2. 자동 커밋 규칙

히스토리 파일(`history/YYYY-MM-DD.json`, `history/fng_log.csv`) 변경은  
워크플로우가 자동으로 아래 메시지로 커밋합니다:

```
chore: daily history snapshot [skip ci]
```

`[skip ci]` 태그로 재귀 트리거를 방지합니다.

### 4-3. 워크플로우 변경 시 주의사항

- 환경변수 이름(`TELEGRAM_CHAT_IDS` vs `TELEGRAM_CHAT_ID`)을 반드시 앱 코드와 일치시킵니다.
- `permissions` 블록이 없으면 `git push` 시 `403` 에러가 발생합니다.
- 워크플로우 수정 후에는 **Actions 탭**에서 수동 실행(`workflow_dispatch`)으로 검증합니다.

---

## 5. 변경 유형별 작업 절차

### 5-1. 데이터 수집 로직 변경 (`market_data.py`)

1. 변경 구현
2. 로컬에서 `python main.py` 실행 또는 스모크 테스트로 수집 결과 확인
3. 단위 테스트 추가·실행
4. `README.md` 기능 테이블 업데이트 (필요 시)

### 5-2. AI 리포트 변경 (`ai_report.py`)

- 현재 모델: `gemini-2.5-flash`
- 프롬프트·모델 변경 시 스모크 테스트로 리포트 품질 확인 후 커밋

### 5-3. 텔레그램 전송 변경 (`telegram_sender.py`, `config.py`)

- 수신자 파싱 로직 변경 시 `test_config.py`에 파싱 케이스 추가
- 중복 chat ID 처리 여부, 발송 실패 시 동작 확인

### 5-4. 차트 변경 (`chart.py`)

- 로컬(Windows)과 GitHub Actions(Ubuntu) 간 폰트 차이 주의
- Ubuntu: `fonts-nanum` 패키지 사용 (워크플로우에서 자동 설치)
- Windows: `Malgun Gothic` 사용

### 5-5. GitHub Actions 워크플로우 변경

- 변경 후 수동 실행으로 검증
- 환경변수·Secrets 이름 변경 시 `CONTEXT.md` 및 `README.md`도 동시 업데이트

---

## 6. 코딩 컨벤션

- 변경은 최소화·외과적으로 (관련 없는 코드는 건드리지 않음)
- 기존 동작은 명확한 버그가 아니면 유지
- 암묵적 폴백보다 명시적 검증 선호
- 동작·설정 변경 시 문서(`README.md`, `CONTEXT.md`, `CHANGELOG.md`) 동시 업데이트
- 파싱·설정 변경에는 소규모 단위 테스트 추가

---

## 7. Copilot 세션 간 인수인계 체크리스트

새 세션 시작 시 아래 파일을 순서대로 확인합니다:

1. `CHANGELOG.md` — 최근 변경사항 파악
2. `CONTEXT.md` — 아키텍처, 환경변수, 디버깅 가이드
3. `WORKFLOW.md` — 이 문서 (작업 절차 확인)
4. `README.md` — 사용자 대면 문서 최신 여부 확인
5. `.github/workflows/daily_report.yml` — CI/CD 현재 상태 확인
