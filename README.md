# PPC Competitive Dashboard

## Live Dashboard

https://statlas.prod.atl-paas.net/ppc-competitive-dashboard/index.html

## Source Data

Source exports live in `data/source/`:

- `ppc-spend.csv` — monthly PPC spend by domain
- `paid-clicks.csv` — monthly paid clicks by domain

The dashboard is a single static `index.html`. Data is embedded directly into that file.

## Refresh

```bash
python3 scripts/from_csv.py
```

The script:

- Reads spend and paid-clicks CSVs
- Normalizes domains into dashboard brands
- Calculates spend share from monthly spend
- Calculates CPC as `spend / paid clicks`
- Rewrites the embedded arrays in `index.html`

## Data Watchout

The current spend export uses `jira.atlassian.com` and `confluence.atlassian.com`, while the
paid-clicks export uses `atlassian.com/software/jira` and `atlassian.com/software/confluence`.
If the spend source does not include the same Atlassian URL set, Jira and Confluence CPC will
look artificially low.
