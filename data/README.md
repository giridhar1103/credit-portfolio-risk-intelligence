# Data directory

The raw LendingClub file is intentionally excluded from Git because it is large and should remain immutable.

Expected source path:

```text
data/raw/accepted_2007_to_2018Q4.csv
```

Download the pinned public mirror and verify its published checksum:

```bash
./scripts/download_data.sh
```

`source_manifest.json` records the source page, exact file size, checksum, schema width, and
retrieval date. This makes the analysis reproducible even if a hosting page changes later.

The validation command checks the required schema before any analytical tables are built:

```bash
credit-risk validate-data --deep
```

The deep validation report captures:

- source path;
- file size;
- SHA-256 checksum;
- total data-row count;
- required and missing columns.

Generated databases and exports are written under `data/processed/` and `data/powerbi/`. They are reproducible and are not committed by default.

`credit-risk export-web` writes a deterministic aggregate-only dashboard bundle to `data/web/`.
The bundle is safe for a public frontend because it contains governed marts rather than loan-level
records, but it remains generated and uncommitted by default.
