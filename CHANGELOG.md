# Changelog

이 프로젝트의 모든 주요 변경사항을 이 파일에 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

---

## [Unreleased]

---

## [2026-03-19b]

### Changed
- `ai_report.py`: Gemini API 호출 방식을 단일 프롬프트 문자열에서 `system_instruction` + `contents` 분리 방식으로 전환
  - `build_system_instruction()`: 전문가 지침, 분석 사고 흐름, 출력 구조, 마크다운 규칙을 시스템 레벨로 분리
  - `build_user_content()`: 오늘의 시장 데이터와 리포트 작성 요청만 포함
  - `GenerateContentConfig(system_instruction=...)` 파라미터로 SDK 내부 최적화 활용

### Removed
- `ai_report.py`: 미사용 상태였던 공포·탐욕 지수 기반 페르소나 기능(`get_persona_instruction`) 제거
- `ai_report.py`: `get_expert_guidelines()` 및 `build_prompt()` 함수 제거 (역할을 분리된 함수들로 대체)

---

## [2026-03-19]

### Fixed
- GitHub Actions `Commit history` 스텝에서 `403` 권한 오류 수정
  - `.github/workflows/daily_report.yml` 의 `build` job에 `permissions: contents: write` 추가
  - 기본 `GITHUB_TOKEN`이 read-only로 동작하여 `git push`가 거부되던 문제 해소

---

<!-- 변경사항 작성 가이드
## [YYYY-MM-DD]

### Added       — 새로운 기능 추가
### Changed     — 기존 기능 변경
### Deprecated  — 곧 삭제될 기능
### Removed     — 삭제된 기능
### Fixed       — 버그 수정
### Security    — 보안 취약점 수정
-->
