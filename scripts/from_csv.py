#!/usr/bin/env python3
"""Regenerate the static PPC dashboard from the Similarweb exports in data/source/."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source"
SPEND_CSV = SOURCE / "PPC Spend.csv"
CLICKS_CSV = SOURCE / "Paid Clicks.csv"
OUT = ROOT / "index.html"

BRAND_ORDER = [
    "Jira",
    "Confluence",
    "Atlassian",
    "Wrike",
    "Smartsheet",
    "Notion",
    "ClickUp",
    "Asana",
    "Monday.com",
    "Linear",
]

COLUMNS = {
    "atlassian.com": "Atlassian",
    "atlassian.com/software/jira": "Jira",
    "atlassian.com/software/confluence": "Confluence",
    "wrike.com": "Wrike",
    "smartsheet.com": "Smartsheet",
    "notion.com": "Notion",
    "clickup.com": "ClickUp",
    "asana.com": "Asana",
    "monday.com": "Monday.com",
    "linear.app": "Linear",
}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def number(value: str | None) -> float:
    value = (value or "").strip()
    if not value or value.lower() in {"null", "nan"}:
        return 0.0
    return float(value)


def read_metric(path: Path, columns: dict[str, str]) -> tuple[list[str], dict[str, list[float]]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise SystemExit(f"Missing header row in {path}")

        missing = sorted(set(columns) - set(reader.fieldnames))
        if missing:
            raise SystemExit(f"Missing columns in {path}: {', '.join(missing)}")

        months: list[str] = []
        values = {name: [] for name in columns.values()}
        for row in reader:
            month = (row.get(reader.fieldnames[0]) or "").strip()
            if not month:
                continue
            months.append(month)
            for column, name in columns.items():
                values[name].append(number(row.get(column)))

    return months, values


def js_array(values: list[float] | list[str]) -> str:
    return json.dumps(values, separators=(",", ":"))


def js_object(values: dict[str, list[float]], digits: int) -> str:
    lines = ["{"]
    for brand in BRAND_ORDER:
        rounded = [round(value, digits) for value in values[brand]]
        lines.append(f'      {json.dumps(brand)}: {js_array(rounded)},')
    lines.append("    }")
    return "\n".join(lines)


def format_month(label: str) -> str:
    year, month = label.split("-")
    return f"{MONTH_NAMES[int(month) - 1]} '{year[-2:]}"


def format_period(label: str) -> str:
    year, month = label.split("-")
    return f"{MONTH_NAMES[int(month) - 1]} {year}"


def replace_const(text: str, name: str, value: str) -> str:
    pattern = rf"const {name} = .*?;\n"
    replacement = f"const {name} = {value};\n"
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Could not find const {name} in {OUT}")
    return updated


def main() -> None:
    spend_months, spend = read_metric(SPEND_CSV, COLUMNS)
    click_months, clicks = read_metric(CLICKS_CSV, COLUMNS)
    if spend_months != click_months:
        raise SystemExit(f"Month mismatch:\nspend={spend_months}\nclicks={click_months}")

    html = OUT.read_text(encoding="utf-8")
    period = f"{format_period(spend_months[0])} – {format_period(spend_months[-1])}"
    html = replace_const(html, "PERIOD_LABEL", json.dumps(period, ensure_ascii=False))
    html = replace_const(html, "MONTHS", js_array([format_month(month) for month in spend_months]))
    html = replace_const(html, "SPEND_USD", js_object(spend, digits=0))
    html = replace_const(html, "PAID_CLICKS", js_object(clicks, digits=0))
    note_period = period.replace("–", "&ndash;")
    html, notes = re.subn(r'(<p class="chart-note">).*?( &middot; 100% stacked)', rf"\g<1>{note_period}\g<2>", html)
    if notes == 0:
        raise SystemExit(f"Could not find chart notes in {OUT}")
    OUT.write_text(html, encoding="utf-8")

    print(f"Wrote {OUT}")
    print(f"Months: {spend_months[0]} to {spend_months[-1]}")
    for brand in BRAND_ORDER:
        print(f"{brand:12} spend={sum(spend[brand]):>14,.0f}  latest_clicks={clicks[brand][-1]:>12,.0f}")


if __name__ == "__main__":
    main()
