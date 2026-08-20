# Hosted analytics architecture

## Public routes

- `/projects/credit-risk`: recruiter-facing case study and methodology narrative.
- `/dashboards/credit-risk`: interactive portfolio and scenario dashboard.
- GitHub repository: implementation, tests, SQL lineage, and reproducibility evidence.

## Initial serving design

The first hosted version should be static-first:

```text
Raw 2.26M-row CSV (private to pipeline)
                |
                v
        DuckDB governed marts
                |
                v
  aggregate-only dashboard JSON
                |
                v
 Cloudflare-hosted frontend route
```

Run:

```bash
credit-risk export-web
```

This writes `data/web/credit-risk-dashboard.json`. The bundle includes eleven governed tables,
methodology metadata, and reconciliation status. It contains no loan-level rows and is suitable for
copying into the frontend's public asset directory.

## Why static-first

- The source is historical, so a live transactional backend would imply freshness that does not
  exist.
- The dashboard needs fewer than one thousand aggregate rows, not 2.26 million browser records.
- Static assets are simple to cache, inexpensive to serve, and easy to version with the case study.
- All filtering required for the first release can run client-side over the governed aggregate
  bundle.

## When to add a Worker and D1

Add a small Worker API and D1 only if the product later needs saved user scenarios, server-side
scenario calculations, analytics events, or multiple dataset versions. Do not place the raw loan
table in D1 or expose unrestricted SQL endpoints.

Suggested future endpoints:

- `GET /api/credit-risk/v1/summary`
- `GET /api/credit-risk/v1/segments?type=grade`
- `GET /api/credit-risk/v1/vintages?scope=fully_matured`
- `POST /api/credit-risk/v1/scenarios` with bounded, validated PD/LGD inputs

## Publishing controls

- Block export if any warehouse reconciliation fails.
- Display population and observation dates beside every KPI.
- Label observed results, calculated proxies, and scenario assumptions separately.
- Never publish raw loan rows or imply that the historical extract is live production data.
- Version the JSON contract before changing field meanings.
