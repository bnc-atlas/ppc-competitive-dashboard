# PPC Competitive Dashboard

## Live Dashboard

https://statlas.prod.atl-paas.net/ppc-competitive-dashboard/index.html

## Dashboard Views

The static dashboard contains two tabs, each with two monthly 100% stacked bar charts:
**Paid search market share by PPC spend** and **Paid clicks market share**.

1. **Atlassian** — uses the `atlassian.com` domain and excludes Jira and Confluence.
2. **By product** — uses the `atlassian.com/software/jira` and `atlassian.com/software/confluence`
   URL prefixes and excludes `atlassian.com`.

Shares are normalized within each tab's set so the displayed entities sum to 100%.

## Source Data

All data is Similarweb, worldwide, monthly. Files live in `data/source/`:

- `PPC Spend.csv` — PPC spend (USD) per entity: atlassian.com, the Jira and Confluence URL prefixes,
  asana.com, clickup.com, monday.com, notion.com, smartsheet.com, wrike.com, linear.app
- `Paid Clicks.csv` — paid clicks per entity for the same ten entities

Both are Similarweb web-app exports. The Similarweb API returns no data for the Jira and Confluence
URL prefixes, so those columns have to come from the exports. Earlier pulls are in `data/archive/`.

Notion is tracked as `notion.com`. Its ads moved off `notion.so`, which reads as near zero from late 2025.

## Refresh

Replace both files in `data/source/` with the new exports (same column headers), then run:

```bash
python3 scripts/from_csv.py
```

The script validates that both files cover the same months, maps source headers to display names,
and rewrites the embedded data arrays, period label, and chart date notes in `index.html`.
