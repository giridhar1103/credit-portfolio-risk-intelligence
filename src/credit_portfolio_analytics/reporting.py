"""Generate a concise executive credit-risk review from warehouse marts."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import ProjectConfig


def _row_as_dict(cursor: Any) -> dict[str, Any]:
    row = cursor.fetchone()
    if row is None:
        raise ValueError("Required warehouse result is empty")
    return {item[0]: value for item, value in zip(cursor.description, row, strict=True)}


def _money(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if absolute >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def _percent(value: float) -> str:
    return f"{100 * value:.2f}%"


def _comparison_lines(connection: Any, minimum_loans: int) -> list[str]:
    rows = connection.execute(
        """
        SELECT segment_type, segment_value, loans, default_rate
        FROM mart_segment_performance
        WHERE segment_type IN ('grade', 'interest_rate_band', 'dti_band', 'term', 'purpose')
          AND loans >= ?
        ORDER BY segment_type, default_rate
        """,
        [minimum_loans],
    ).fetchall()
    grouped: dict[str, list[tuple[str, int, float]]] = defaultdict(list)
    for segment_type, segment_value, loans, default_rate in rows:
        grouped[segment_type].append((segment_value, loans, default_rate))

    labels = {
        "grade": "Grade",
        "interest_rate_band": "Interest-rate band",
        "dti_band": "DTI band",
        "term": "Term",
        "purpose": "Purpose",
    }
    lines: list[str] = []
    for segment_type in ["grade", "interest_rate_band", "dti_band", "term", "purpose"]:
        segments = grouped.get(segment_type, [])
        if len(segments) < 2:
            continue
        low_name, low_loans, low_rate = segments[0]
        high_name, high_loans, high_rate = segments[-1]
        multiple = high_rate / low_rate if low_rate else 0
        lines.append(
            f"- **{labels[segment_type]}:** {low_name} was {_percent(low_rate)} "
            f"(n={low_loans:,}) versus {high_name} at {_percent(high_rate)} "
            f"(n={high_loans:,}), a {100 * (high_rate - low_rate):.2f} pp gap and "
            f"{multiple:.2f}x risk multiple."
        )
    return lines


def render_executive_report(config: ProjectConfig, *, minimum_segment_loans: int = 1_000) -> str:
    """Render the review as Markdown using only reconciled warehouse tables."""
    import duckdb

    if not config.warehouse_path.exists():
        raise FileNotFoundError(f"Warehouse not found: {config.warehouse_path}")

    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        summary = _row_as_dict(connection.execute("SELECT * FROM mart_executive_summary"))
        quality = dict(
            connection.execute("SELECT metric, value FROM mart_data_quality_summary").fetchall()
        )
        economics = _row_as_dict(
            connection.execute("SELECT * FROM mart_credit_economics_summary")
        )
        open_book = _row_as_dict(connection.execute("SELECT * FROM mart_open_book_summary"))
        open_grade_rows = connection.execute(
            """
            SELECT segment_value, loans, delinquent_exposure_rate
            FROM mart_open_book_segments
            WHERE segment_type = 'grade'
              AND loans >= ?
              AND delinquent_exposure_rate IS NOT NULL
            ORDER BY delinquent_exposure_rate
            """,
            [minimum_segment_loans],
        ).fetchall()
        scenarios = connection.execute(
            """
            SELECT scenario_name, expected_loss, expected_loss_rate,
                   expected_loss_change, expected_loss_relative_change,
                   expected_loss_rate_change_pp, exposure_weighted_pd,
                   exposure_weighted_lgd
            FROM mart_expected_loss_summary
            ORDER BY pd_multiplier
            """
        ).fetchall()
        comparisons = _comparison_lines(connection, minimum_segment_loans)
        high_tail = _row_as_dict(
            connection.execute(
                """
                WITH eligible AS (
                    SELECT *
                    FROM fact_loan
                    WHERE is_model_eligible
                      AND is_contractually_mature
                      AND issue_date IS NOT NULL
                      AND funded_amount IS NOT NULL
                )
                SELECT
                    count(*) FILTER (WHERE grade IN ('E', 'F', 'G')) AS loans,
                    sum(funded_amount) FILTER (WHERE grade IN ('E', 'F', 'G')) AS exposure,
                    sum(is_default_strict::INTEGER)
                        FILTER (WHERE grade IN ('E', 'F', 'G')) AS defaults,
                    count(*) AS portfolio_loans,
                    sum(funded_amount) AS portfolio_exposure,
                    sum(is_default_strict::INTEGER) AS portfolio_defaults
                FROM eligible
                """
            )
        )
        top_purpose = _row_as_dict(
            connection.execute(
                """
                SELECT segment_value, exposure_share, default_contribution
                FROM mart_segment_performance
                WHERE segment_type = 'purpose'
                ORDER BY default_contribution DESC
                LIMIT 1
                """
            )
        )
    finally:
        connection.close()

    raw_rows = int(quality["raw_rows"])
    resolved_rows = int(summary["resolved_loans"])
    matured_rows = int(summary["matured_loans"])
    exposure_rate_delta = (
        summary["matured_exposure_default_rate"] - summary["resolved_exposure_default_rate"]
    )
    exposure_rate_relative = exposure_rate_delta / summary["resolved_exposure_default_rate"]

    high_tail_exposure_share = high_tail["exposure"] / high_tail["portfolio_exposure"]
    high_tail_default_share = high_tail["defaults"] / high_tail["portfolio_defaults"]
    open_grade_line = ""
    if len(open_grade_rows) >= 2:
        low_grade, low_grade_loans, low_delinquency = open_grade_rows[0]
        high_grade, high_grade_loans, high_delinquency = open_grade_rows[-1]
        open_grade_line = (
            f"- Open-book delinquent EAD ranges from **{_percent(low_delinquency)} for grade "
            f"{low_grade}** (n={low_grade_loans:,}) to **{_percent(high_delinquency)} for grade "
            f"{high_grade}** (n={high_grade_loans:,}), a "
            f"**{high_delinquency / low_delinquency:.2f}x spread**."
        )

    scenario_lines = []
    for (
        name,
        loss,
        rate,
        change,
        relative_change,
        rate_change_pp,
        weighted_pd,
        weighted_lgd,
    ) in scenarios:
        if change == 0:
            scenario_lines.append(
                f"- **{name}:** {_money(loss)} expected loss, or {_percent(rate)} of EAD "
                f"(weighted PD {_percent(weighted_pd)}; weighted LGD "
                f"{_percent(weighted_lgd)})."
            )
        else:
            scenario_lines.append(
                f"- **{name}:** {_money(loss)}, an increase of {_money(change)} "
                f"({relative_change:.2%}) and {rate_change_pp:.2f} pp versus baseline."
            )

    comparison_text = "\n".join(comparisons) if comparisons else (
        "- No segment comparison met the configured minimum sample threshold."
    )
    scenario_text = "\n".join(scenario_lines)

    snapshot_date = config.snapshot_date.isoformat()
    observation_date = config.source_observation_date.isoformat()
    return f"""# Executive credit risk review

_Generated from the DuckDB analytical marts. Snapshot assumption: {snapshot_date}._

## Executive summary

- The source contains **{raw_rows:,} accepted-loan records**. Strict resolved outcomes retain
  **{resolved_rows:,} loans ({resolved_rows / raw_rows:.2%})**; the contractual-maturity rule
  retains **{matured_rows:,} loans ({matured_rows / raw_rows:.2%} of raw and
  {summary['matured_population_retention_rate']:.2%} of resolved)**.
- The default rate changes from **{_percent(summary['resolved_default_rate'])}** on all resolved
  loans to **{_percent(summary['matured_default_rate'])}** on fully matured loans: a
  **{summary['default_rate_change_pp']:.2f} pp ({summary['default_rate_relative_change']:.2%})**
  change. This quantifies incomplete-maturity bias rather than treating the two populations as
  interchangeable.
- On a funded-principal basis, the exposure default rate changes from
  **{_percent(summary['resolved_exposure_default_rate'])}** to
  **{_percent(summary['matured_exposure_default_rate'])}**, a
  **{100 * exposure_rate_delta:.2f} pp ({exposure_rate_relative:.2%})** change.
- The primary decision population is **{matured_rows:,} loans** representing
  **{_money(summary['matured_exposure'])}** in funded principal and
  **{int(summary['matured_defaults']):,} strict defaults**.

## Credit economics

- Fully matured loans generated **{_money(economics['interest_received'])}** of recorded interest
  and **{_money(economics['net_credit_loss'])}** of net credit loss after recoveries and collection
  costs.
- Net credit loss equals **{_percent(economics['net_credit_loss_rate'])} of funded exposure**.
  Charged-off principal produced a **{_percent(economics['observed_recovery_rate'])} net recovery
  rate** and **{_percent(economics['observed_lgd_proxy'])} observed LGD proxy**.
- The non-annualized net cash return proxy is
  **{_percent(economics['net_cash_return_proxy'])}**. It is a cash multiple-derived diagnostic,
  not IRR, APR, profit, or an accounting return.
- Credit loss consumed **{_percent(economics['loss_to_interest_ratio'])} of recorded interest**,
  leaving a pre-funding-cost pricing-cushion proxy of
  **{_percent(economics['pricing_cushion_proxy'])} of funded exposure**.

## Open-book risk position

The source observation month is **{observation_date}**, inferred from the latest operational date
available in the extract; it is separate from the conservative historical maturity cutoff above.

- **{int(open_book['loans']):,} open accounts** carry
  **{_money(open_book['outstanding_exposure'])} of outstanding-principal EAD**.
- Delinquent accounts represent **{int(open_book['delinquent_loans']):,} loans** and
  **{_money(open_book['delinquent_exposure'])}**, or
  **{_percent(open_book['delinquent_exposure_rate'])} of open EAD**.
- The open book has an exposure-weighted contractual rate of
  **{open_book['weighted_average_interest_rate']:.2f}%** and weighted seasoning of
  **{open_book['exposure_weighted_months_on_book']:.1f} months**.
{open_grade_line}

## Risk segmentation

Comparisons below are descriptive and include only segments with at least
{minimum_segment_loans:,} matured loans.

{comparison_text}

- Grades E-G represent **{high_tail_exposure_share:.2%} of exposure** but
  **{high_tail_default_share:.2%} of defaults** ({int(high_tail['defaults']):,} defaults).
- **{top_purpose['segment_value']}** is the largest purpose-level source of defaults:
  **{top_purpose['default_contribution']:.2%} of defaults** against
  **{top_purpose['exposure_share']:.2%} of exposure**.

## Expected-loss sensitivity

Expected loss uses open-book outstanding principal x smoothed historical grade PD x scenario
multiplier x smoothed observed grade LGD. It is a lifetime benchmark sensitivity, not a company
forecast or CECL estimate.

{scenario_text}

## Management actions

1. Review pricing, limits, and manual-review rules for the E-G tail; it contributes a larger share
   of defaults than exposure.
2. Prioritize delinquent open exposure and add term and affordability overlays to monitoring,
   while validating that observed differences persist after controlling for vintage and mix.
3. Use scenario increments as transparent loss-capacity sensitivities and
   replace grade-level benchmark PDs with temporally validated borrower-level probabilities before
   any production decision.

## Interpretation limits

- The file contains originated loans, not all applications, so it cannot estimate approval effects.
- Associations are descriptive and should not be presented as causal drivers.
- Maturity filtering improves outcome comparability but also changes vintage and term composition.
- Open-book EAD uses recorded outstanding principal; the extract does not provide balance at the
  future date of default.
- Historical grade PD is an origination-lifetime benchmark, not a conditional remaining-life PD.
- The cash-return proxy is not annualized and excludes funding and operating costs.
- Public historical data and transparent assumptions make this a portfolio analytics project, not
  a production credit policy or accounting loss estimate.
"""


def write_executive_report(
    config: ProjectConfig,
    output_path: Path | None = None,
    *,
    minimum_segment_loans: int = 1_000,
) -> Path:
    """Write the generated Markdown review and return its resolved path."""
    default_path = config.repo_root / "reports" / "executive_credit_review.md"
    destination = (output_path or default_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_executive_report(config, minimum_segment_loans=minimum_segment_loans),
        encoding="utf-8",
    )
    return destination
