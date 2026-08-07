#!/usr/bin/env python3
"""Regenerate the single-file dashboard from local spend and paid-click CSVs."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEND_CSV = ROOT / "data" / "source" / "ppc-spend.csv"
CLICKS_CSV = ROOT / "data" / "source" / "paid-clicks.csv"
OUT = ROOT / "index.html"

BRAND_ORDER = [
    "Confluence",
    "Jira",
    "Wrike",
    "Smartsheet",
    "Notion",
    "ClickUp",
    "Asana",
    "Monday.com",
    "Linear",
]

DOMAIN_TO_BRAND = {
    "Confluence": "Confluence",
    "confluence.atlassian.com": "Confluence",
    "atlassian.com/software/confluence": "Confluence",
    "Jira": "Jira",
    "jira.atlassian.com": "Jira",
    "atlassian.com/software/jira": "Jira",
    "Wrike": "Wrike",
    "wrike.com": "Wrike",
    "Smartsheet": "Smartsheet",
    "smartsheet.com": "Smartsheet",
    "Notion": "Notion",
    "notion.so": "Notion",
    "ClickUp": "ClickUp",
    "clickup.com": "ClickUp",
    "Asana": "Asana",
    "asana.com": "Asana",
    "Monday.com": "Monday.com",
    "monday.com": "Monday.com",
    "Linear": "Linear",
    "linear.app": "Linear",
}


def num(value: str) -> float:
    value = (value or "").strip()
    if not value or value.lower() == "null":
        return 0.0
    return float(value)


def read_metric(path: Path) -> tuple[list[str], dict[str, list[float]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    header = rows[0]
    months = [row[0] for row in rows[1:]]
    out = {brand: [0.0 for _ in months] for brand in BRAND_ORDER}

    for col_idx, domain in enumerate(header[1:], start=1):
        brand = DOMAIN_TO_BRAND.get(domain)
        if not brand:
            continue
        for row_idx, row in enumerate(rows[1:]):
            out[brand][row_idx] += num(row[col_idx] if col_idx < len(row) else "")

    return months, out


def js_array(values) -> str:
    return json.dumps(values, separators=(",", ":"))


def js_obj(obj: dict[str, list[float]], digits: int = 2) -> str:
    lines = ["{"]
    for brand in BRAND_ORDER:
        values = [round(v, digits) for v in obj[brand]]
        lines.append(f'  "{brand}": {js_array(values)},')
    lines.append("}")
    return "\n".join(lines)


def fmt_month(label: str) -> str:
    year, month = label.split("-")
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{names[int(month) - 1]} '{year[-2:]}"


def fmt_period(label: str) -> str:
    year, month = label.split("-")
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{names[int(month) - 1]} {year}"


def replace_const(text: str, name: str, value: str) -> str:
    pattern = rf"const {name} = .*?;\n"
    return re.sub(pattern, f"const {name} = {value};\n", text, flags=re.S)


def main() -> None:
    spend_months, spend = read_metric(SPEND_CSV)
    click_months, clicks = read_metric(CLICKS_CSV)
    if spend_months != click_months:
        raise SystemExit(f"Month mismatch:\nspend={spend_months}\nclicks={click_months}")

    monthly_totals = [sum(spend[brand][i] for brand in BRAND_ORDER) for i in range(len(spend_months))]
    spend_share = {
        brand: [
            round((spend[brand][i] / monthly_totals[i]) * 100, 1) if monthly_totals[i] else 0.0
            for i in range(len(spend_months))
        ]
        for brand in BRAND_ORDER
    }

    html = OUT.read_text()
    period = f"{fmt_period(spend_months[0])} – {fmt_period(spend_months[-1])}"
    html = re.sub(r"(Paid search competitive analysis &middot; Worldwide &middot; ).*?(</p>)", rf"\1{period}\2", html)
    html = re.sub(r"Period total .*? &middot;", f"Period total {period} &middot;", html)
    html = html.replace("Period total &middot; hover bars", f"Period total {period} &middot; hover bars")

    html = replace_const(html, "BRANDS", js_array(BRAND_ORDER))
    html = replace_const(html, "MONTHS", js_array([fmt_month(m) for m in spend_months]))
    html = replace_const(html, "MONTHLY_SPEND", js_obj(spend, digits=2))
    html = replace_const(html, "SPEND_SHARE_PCT", js_obj(spend_share, digits=1))
    html = replace_const(html, "TOTAL_CLICKS", js_obj(clicks, digits=2))
    html = re.sub(
        r"const PAID_SHARE = \{.*?\};\n\n",
        "",
        html,
        flags=re.S,
    )
    html = re.sub(
        r"const paidClicks = TOTAL_CLICKS\[b\]\.reduce\(\(s, v, i\) => s \+ v \* PAID_SHARE\[b\]\[i\], 0\);",
        "const paidClicks = TOTAL_CLICKS[b].reduce((s, v) => s + v, 0);",
        html,
    )

    OUT.write_text(html)
    print(f"Wrote {OUT}")
    print(f"Months: {spend_months[0]} to {spend_months[-1]}")
    for brand in BRAND_ORDER:
        brand_spend = sum(spend[brand])
        brand_clicks = sum(clicks[brand])
        cpc = brand_spend / brand_clicks if brand_clicks else 0
        print(f"{brand:12} spend=${brand_spend:,.0f} paid_clicks={brand_clicks:,.0f} cpc=${cpc:.2f}")


if __name__ == "__main__":
    main()
