# Changelog

이 프로젝트의 모든 주요 변경사항을 이 파일에 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

---

## [Unreleased]

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
