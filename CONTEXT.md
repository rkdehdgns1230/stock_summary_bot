# Project Context

## What this project does

This repository runs a daily stock-market summary bot.

It collects:
- CNN Fear & Greed index
- U.S. market indicators
- KOSPI200 futures data
- Naver Finance news headlines and article body text (top 5 articles)

It then:
- generates a Korean summary with Gemini
- renders a fear/greed gauge image
- sends both the image and report to Telegram

## Main files

- `main.py`: orchestration entry point
- `market_data.py`: market/news data collection
- `ai_report.py`: Gemini prompt + summary generation
- `chart.py`: fear/greed gauge rendering and font handling
- `telegram_sender.py`: Telegram message/photo delivery
- `config.py`: environment-variable loading and normalization
- `.github/workflows/daily_report.yml`: scheduled GitHub Actions execution

## History storage

The bot saves two files to the `history/` directory on every **scheduled** run.
Smoke test runs (`TEST_TELEGRAM_CHAT_ID` set) skip history saving entirely.

| File | Format | Content |
|------|--------|---------|
| `history/YYYY-MM-DD.json` | JSON | Full snapshot: F&G score/stage, all market data strings, news, raw AI report |
| `history/fng_log.csv` | CSV | Running log: date, score, stage — one row per day |

**Deduplication**: if the scheduled run is retried on the same date, the JSON is overwritten and the CSV row is updated in place (upsert). This prevents duplicate entries regardless of how many times the workflow is triggered.

`daily_report.yml` auto-commits the updated files with the message `chore: daily history snapshot [skip ci]`. The `[skip ci]` tag prevents a re-trigger loop.

## Smoke test (E2E, single recipient)

To run the full pipeline against real APIs but send only to a single Telegram chat:

**Locally:**
```bash
TEST_TELEGRAM_CHAT_ID=your_chat_id python main.py
```

**GitHub Actions (manual):**
1. Add `TEST_TELEGRAM_CHAT_ID` to repository secrets.
2. Trigger the "Smoke Test (Single Recipient)" workflow manually from the Actions tab.

When `TEST_TELEGRAM_CHAT_ID` is set, `config._get_effective_chat_ids()` returns only that single ID, overriding `TELEGRAM_CHAT_IDS` for the duration of the run.

## Runtime flow

1. `main.py` gathers market, index, and news data.
2. `chart.py` creates the gauge image.
3. `ai_report.py` produces the Korean report text.
4. `telegram_sender.py` sends the image first, then the text report.

## Environment variables

Required:
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_IDS`
- `GEMINI_API_KEY`

Compatibility fallback:
- `config.py` also accepts legacy `TELEGRAM_CHAT_ID` if `TELEGRAM_CHAT_IDS` is not present.

Accepted `TELEGRAM_CHAT_IDS` formats:
- comma-separated string: `123456789,987654321`
- newline-separated string
- JSON-like list string: `["123456789", "987654321"]`

## GitHub Actions context

The production-style scheduled run is defined in `.github/workflows/daily_report.yml`.

Important lesson from a recent bug:
- application code was updated to read `TELEGRAM_CHAT_IDS`
- GitHub Actions was still passing `TELEGRAM_CHAT_ID`
- result: parsing looked broken, but the actual issue was env-name mismatch between app code and workflow config

Current workflow behavior:
- prefer `secrets.TELEGRAM_CHAT_IDS`
- fall back to `secrets.TELEGRAM_CHAT_ID` for backward compatibility

Safest GitHub Actions secret value for multiple targets:

```text
["6530415022","1234567890"]
```

This is safer than relying on manual comma formatting because it is explicit and easier to visually verify.

## Review checklist before concluding a fix

When changing config, delivery, or workflow behavior, always review all connected surfaces:

1. `config.py`
2. call sites that consume the config
3. `.github/workflows/*.yml`
4. `README.md`
5. existing tests and any missing targeted tests

Do not assume the bug is only in the Python code. For this repository, workflow/env mismatches are a realistic failure mode.

## Practical change checklist

Before committing:
- verify env variable names match between code, docs, and workflow files
- verify fallback behavior if keeping backward compatibility
- run `python -m unittest -q`
- inspect `git diff` to confirm only intended files changed

When touching Telegram delivery:
- confirm whether duplicate chat IDs should duplicate delivery or be deduplicated
- verify whether a failure is caused by chat ID parsing, missing secrets, or Telegram API response content

When touching chart rendering:
- keep cross-platform font behavior in mind
- GitHub Actions runs on Ubuntu, so Linux font availability matters

## Working assumptions and conventions

- keep changes surgical and avoid unrelated refactors
- preserve existing behavior unless there is a clear bug
- prefer explicit validation over silent fallback
- update docs when behavior or required configuration changes
- add small targeted tests for parsing or configuration changes

## Suggested debugging order for future sessions

If Telegram delivery fails:

1. inspect `config.py`
2. inspect `telegram_sender.py`
3. inspect `.github/workflows/daily_report.yml`
4. inspect secret names and value shape
5. run tests
6. if needed, add a targeted parser test before changing behavior

If a change seems correct but production still fails, compare:
- local assumptions
- workflow env injection
- actual secret names

That comparison would have caught the recent `TELEGRAM_CHAT_IDS` issue faster.
