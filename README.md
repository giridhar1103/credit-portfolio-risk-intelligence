# Credit Portfolio Risk Analytics


An analyst-focused consumer credit portfolio project built around measurable business outcomes:
portfolio quality, maturity bias, risk concentration, credit economics, open-book exposure,
expected loss, and scenario sensitivity. The project uses the public LendingClub accepted-loan
dataset covering originations from 2007 through 2018 Q4.

## Business question

A consumer lender's Head of Credit Risk needs to know:

- Is portfolio credit quality improving or deteriorating?
- Which vintages and borrower segments contribute the most risk?
- How much do immature loan cohorts distort reported default rates?
- How much loss should the portfolio expect under baseline and adverse assumptions?
- Did additional interest compensate for higher net credit loss?
- How much outstanding exposure is current, delinquent, or already in default?
- Which metrics should management monitor and which actions should it consider?

## Measurable outputs

The pipeline is designed to publish explicit comparisons rather than generic observations:

- raw records to analytically eligible records, including the retained percentage;
- reported default rate to maturity-adjusted default rate, in percentage points and relative percent;
- safest segment to riskiest segment, including risk multiple;
- earliest vintage to latest comparable vintage;
- baseline expected loss to moderate and severe expected loss;
- later phases: baseline model to final model, raw to calibrated probabilities, and first-year to last-year performance.

No portfolio result is hardcoded. Published numbers are generated from SQL tables and exported to CSV for reconciliation and dashboarding.

## Verified first findings

The full-file build currently shows:

- **2,260,701** accepted-loan records, of which **1,348,099** have strict resolved outcomes and
  **676,302** also meet the contractual-maturity rule;
- default rate changes from **19.98% to 14.87%** after maturity adjustment, a
  **5.11 percentage-point / 25.59% relative decrease**;
- default rate ranges from **5.50% for grade A to 37.43% for grade G**, a **6.80x** spread;
- **907,904 open accounts** carry **$9.51B outstanding-principal EAD**, including **$384.2M** of
  delinquent exposure;
- historical net credit loss was **$715.7M** after recoveries and collection costs, consuming
  **46.42% of recorded interest** in the fully matured population;
- the open-book severe scenario increases expected loss by **$647.7M** under the documented PD and
  observed-LGD methodology.

See the generated [executive credit risk review](reports/executive_credit_review.md) for the
reconciled results, management actions, and interpretation limits.
The [hosted analytics architecture](docs/hosting_architecture.md) defines the Cloudflare-ready
aggregate contract and recommended public routes.

## Initial architecture

```text
Raw LendingClub CSV
        |
        v
Data-contract validation
        |
        v
DuckDB fact_loan table
        |
        +--> Cohort and maturity marts
        +--> Segment performance marts
        +--> Credit economics and recovery marts
        +--> Open-book exposure marts
        +--> Grade-level PD and LGD benchmarks
        +--> Open-book expected-loss scenarios
        |
        v
Power BI-ready CSV exports
```

## Repository structure

```text
config/                     Project assumptions and scenario definitions
data/raw/                    Local raw source file (not committed)
data/processed/              Generated DuckDB database (not committed)
data/powerbi/                Reconciled dashboard extracts (CSV outputs are committed)
data/web/                    Aggregate-only hosted dashboard bundle (JSON output is committed)
docs/                        Metric catalog, analysis plan, and dashboard specification
reports/                     Generated executive review with verified portfolio findings
powerbi/                     Power BI handoff documentation
sql/                         Auditable warehouse and analytical SQL
src/credit_portfolio_analytics/
                            Python validation and pipeline orchestration
tests/                       Unit and integration tests with a tiny non-production fixture
```

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Place the raw file at:

```text
data/raw/accepted_2007_to_2018Q4.csv
```

Validate the file contract:

```bash
credit-risk validate-data
```

Use `--deep` to calculate the full row count and SHA-256 checksum:

```bash
credit-risk validate-data --deep
```

Build the warehouse and Power BI extracts:

```bash
credit-risk build
```

Generate the executive credit risk review from the reconciled marts:

```bash
credit-risk report
```

Export the aggregate-only JSON contract for a hosted dashboard:

```bash
credit-risk export-web
```

Generated outputs include:

- `data/processed/credit_portfolio.duckdb`
- `data/powerbi/executive_summary.csv`
- `data/powerbi/vintage_performance.csv`
- `data/powerbi/segment_performance.csv`
- `data/powerbi/credit_economics_summary.csv`
- `data/powerbi/segment_economics.csv`
- `data/powerbi/open_book_summary.csv`
- `data/powerbi/open_book_segments.csv`
- `data/powerbi/expected_loss_summary.csv`
- `data/powerbi/expected_loss_scenarios.csv`
- `data/powerbi/data_quality_summary.csv`
- `data/powerbi/reconciliation_checks.csv`
- `reports/executive_credit_review.md`
- `data/web/credit-risk-dashboard.json`

## Target policy

The primary analytical target is deliberately stricter than the original capstone target:

- **Default:** Charged Off, Default, or credit-policy Charged Off.
- **Non-default:** Fully Paid or credit-policy Fully Paid.
- **Delinquent:** Late or In Grace Period; monitored separately and excluded from the primary model target.
- **Current:** excluded from resolved-outcome modeling.

This prevents temporary delinquency from being silently treated as a completed default outcome. The target policy can later be sensitivity-tested.

## Maturity policy

A loan is considered contractually mature when:

```text
issue month + contractual term <= 2018-12-31
```

The pipeline reports results for both resolved loans and the fully matured subset. This comparison quantifies the effect of recent, incompletely observed cohorts.

## Expected-loss policy

The expected-loss mart uses:

```text
Expected loss = outstanding-principal EAD x benchmark PD x scenario multiplier x benchmark LGD
```

Benchmark PD is estimated from fully matured, resolved loans and smoothed toward the overall
historical rate. LGD is estimated from net recoveries on unpaid principal for charged-off loans and
smoothed toward the portfolio result. These grade-level benchmarks are then applied to recorded
outstanding principal on open accounts. Scenario multipliers remain transparent assumptions in
`config/project.toml`; the results are lifetime sensitivities, not company forecasts or CECL
estimates. A temporally validated borrower-level model can later replace the grade benchmark.

## Quality principles

- Preserve raw data locally and never modify it in place.
- Define every KPI once and reconcile dashboard exports to SQL.
- Fail the warehouse build when key grain, cash-flow, EAD, scenario, or LGD checks do not reconcile.
- Distinguish percentage-point changes from relative percentage changes.
- Separate observed outcomes, model estimates, and scenario assumptions.
- Prefer temporal validation to random splitting.
- Do not interpret macroeconomic sensitivity as causal without supporting evidence.

