# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (Python 3.11 required)
pip install -r requirements.txt

# Run all unit tests
python -m unittest discover -s tests -t . -q

# Run the full pipeline (production)
python main.py

# E2E smoke test — full pipeline but sends only to one Telegram chat, skips history saving
TEST_TELEGRAM_CHAT_ID=your_chat_id python main.py
```

## Architecture

This is a daily Korean stock market briefing bot. `main.py` orchestrates a sequential pipeline:

1. **Data collection** (`bot/market_data.py`) — fetches US market indicators (NASDAQ, S&P500, USD/KRW, 10Y yield), commodities (WTI, Gold, DXY), VIX, KOSPI/KOSDAQ via yfinance; scrapes Naver Finance for top 15 news headlines + 5 full article bodies; fetches CNN Fear & Greed index score and stage.

2. **Gauge rendering** (`bot/chart.py`) — renders a semicircular Fear & Greed gauge image using matplotlib. Font is OS-conditional: `Malgun Gothic` on Windows, `NanumGothic` on Linux (installed via `fonts-nanum` in CI).

3. **AI report generation** (`bot/ai_report.py`) — sends all collected data to Gemini 2.5-Flash with Google Search Grounding enabled. Gemini autonomously searches for additional context (ReAct-style). A **second, separate** Gemini call with `response_schema` extracts structured metadata (market direction, confidence, key risks, sector focus) — these two modes cannot share a single API call.

4. **Reflection** — `bot/history_writer.py` loads yesterday's `history/YYYY-MM-DD.json` snapshot and the recent F&G trend from `history/fng_log.csv` so the AI can compare its prior forecast against today's actual data.

5. **History persistence** (`bot/history_writer.py`) — saves a daily JSON snapshot and upserts a row in `history/fng_log.csv`. Both are auto-committed by CI with `[skip ci]` to prevent re-trigger loops. Smoke test runs skip this step entirely.

6. **Telegram delivery** (`bot/telegram_sender.py`) — sends the gauge image first, then the MarkdownV2-sanitized report text to all configured chat IDs.

## Project structure

```
stock-summary-bot/
├── bot/                   # application package
│   ├── config.py          # environment variable parsing
│   ├── market_data.py     # data collection (yfinance, scraping, CNN F&G)
│   ├── ai_report.py       # Gemini report generation + metadata extraction
│   ├── chart.py           # Fear & Greed gauge image rendering
│   ├── history_writer.py  # snapshot persistence and F&G trend loading
│   └── telegram_sender.py # MarkdownV2 sanitization and delivery
├── tests/                 # test package
│   ├── test_config.py
│   └── test_main.py
├── history/               # runtime data (JSON snapshots, fng_log.csv)
├── main.py                # entry point — orchestrates the pipeline
└── requirements.txt
```

## Configuration

`bot/config.py` reads three required environment variables and normalizes them:

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_IDS` | Recipient chat IDs — accepts comma-separated string, newline-separated, or JSON array string |
| `GEMINI_API_KEY` | Google Gemini API key |

`TELEGRAM_CHAT_ID` (singular) is supported as a legacy fallback. When `TEST_TELEGRAM_CHAT_ID` is set, `config._get_effective_chat_ids()` overrides `TELEGRAM_CHAT_IDS` to deliver only to that single ID.

Recommended format for GitHub Actions secrets: `["id1","id2"]` (JSON array string — safest for multi-recipient).

## Testing

Test files: `tests/test_config.py`, `tests/test_main.py`. Framework: `unittest` + `unittest.mock`.

When changing config or parsing logic, add a targeted test in `tests/test_config.py` before changing behavior.

## Key pitfalls

- **Env name mismatch** is a realistic failure mode: always verify that variable names are consistent across `bot/config.py`, call sites, `.github/workflows/*.yml`, and docs. The `TELEGRAM_CHAT_IDS` vs `TELEGRAM_CHAT_ID` mismatch has caused production failures before.
- **Google Search Grounding and `response_schema` cannot be used in the same Gemini API call** — this is why report generation and metadata extraction are two separate calls in `bot/ai_report.py`.
- **GitHub Actions needs `permissions: contents: write`** on the `build` job for the history auto-commit to succeed (otherwise `git push` returns 403).
- **Chart fonts**: local dev uses `Malgun Gothic` (Windows); CI uses `NanumGothic` (Linux). Changes to `bot/chart.py` must account for both.
- When a fix seems correct but production still fails, compare local assumptions, workflow env injection, and actual secret names — this is the recommended debugging sequence.

## Document maintenance

When changing behavior or configuration, update `README.md`, `CONTEXT.md`, and `CHANGELOG.md` in the same commit.

## Git commit conventions

Format: `type: short description` (English, lowercase, imperative mood)

| Type | When to use |
|---|---|
| `feat` | New feature or visible behavior change |
| `fix` | Bug fix |
| `refactor` | Code restructuring with no behavior change |
| `chore` | Dependencies, CI config, non-code maintenance |
| `ci` | Changes to GitHub Actions workflows only |
| `docs` | Documentation-only changes (README, CONTEXT, CLAUDE.md, etc.) |
| `test` | Adding or fixing tests |

**Splitting commits:** Separate concerns into distinct commits when changes are independently meaningful (e.g., a bug fix in `telegram_sender.py` and a prompt improvement in `ai_report.py` are separate commits even if done together).

**Auto-commit exception:** `chore: daily history snapshot [skip ci]` is generated automatically by CI — never write this manually.
