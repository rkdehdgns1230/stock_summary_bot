#!/usr/bin/env python3
"""Aggregates history/ snapshots into docs/data.json for GitHub Pages."""

import csv
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_DIR = ROOT / "history"
DOCS_DIR = ROOT / "docs"


def _parse_num(text):
    """Extract (value, change_pct) from strings like '나스닥: 21995.91 (-0.71%)'."""
    val = re.search(r":\s*([\d,]+\.?\d*)", text)
    chg = re.search(r"\(([+-]?\d+\.?\d*)%\)", text)
    value = float(val.group(1).replace(",", "")) if val else None
    change = float(chg.group(1)) if chg else None
    return value, change


def _parse_market(market):
    r = {}
    for line in market.get("us", "").split("\n"):
        if "나스닥" in line:
            r["nasdaq"], r["nasdaq_chg"] = _parse_num(line)
        elif "S&P500" in line:
            r["sp500"], r["sp500_chg"] = _parse_num(line)
        elif "환율" in line or "USD/KRW" in line:
            r["usdkrw"], r["usdkrw_chg"] = _parse_num(line)
        elif "10년물" in line or "국채" in line:
            r["bond10y"], r["bond10y_chg"] = _parse_num(line)

    vix_str = market.get("vix", "")
    if "VIX" in vix_str:
        r["vix"], r["vix_chg"] = _parse_num(vix_str)

    for line in market.get("commodities", "").split("\n"):
        if "WTI" in line:
            r["wti"], r["wti_chg"] = _parse_num(line)
        elif "Gold" in line or "금(" in line:
            r["gold"], r["gold_chg"] = _parse_num(line)
        elif "DXY" in line or "달러 인덱스" in line:
            r["dxy"], r["dxy_chg"] = _parse_num(line)

    for attr, key in [("kospi", "kospi"), ("kosdaq", "kosdaq")]:
        s = market.get(attr, "")
        if s:
            v, c = _parse_num(s)
            r[key], r[f"{key}_chg"] = v, c

    return r


def _load_fng_log():
    path = HISTORY_DIR / "fng_log.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({"date": row["date"], "score": int(row["score"]), "stage": row["stage"]})
            except (KeyError, ValueError):
                pass
    return sorted(rows, key=lambda x: x["date"])


def _load_daily():
    snapshots = []
    for p in sorted(HISTORY_DIR.glob("????-??-??.json")):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        snapshots.append(
            {
                "date": data.get("date", p.stem),
                "fng_score": data.get("fng_score"),
                "fng_stage": data.get("fng_stage"),
                "market": _parse_market(data.get("market", {})),
                "structured": data.get("structured"),
                "report": data.get("report", ""),
                "news": data.get("news", ""),
            }
        )
    return snapshots


def main():
    DOCS_DIR.mkdir(exist_ok=True)
    payload = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fng_history": _load_fng_log(),
        "daily": _load_daily(),
    }
    out = DOCS_DIR / "data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK {out}  ({len(payload['daily'])} snapshots)")


if __name__ == "__main__":
    main()
