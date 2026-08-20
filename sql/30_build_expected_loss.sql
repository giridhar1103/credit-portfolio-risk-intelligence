CREATE OR REPLACE TABLE dim_grade_risk_benchmark AS
WITH reference AS (
    SELECT *
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND grade IS NOT NULL
      AND funded_amount IS NOT NULL
), grade_universe AS (
    SELECT DISTINCT grade FROM fact_loan WHERE grade IS NOT NULL
), overall AS (
    SELECT
        avg(is_default_strict::INTEGER) AS overall_pd,
        coalesce(
            sum(net_credit_loss) / nullif(sum(gross_principal_shortfall), 0),
            {{fallback_lgd}}
        ) AS overall_lgd
    FROM reference
), grade_stats AS (
    SELECT
        grade,
        count(*) AS reference_loans,
        sum(is_default_strict::INTEGER) AS defaults,
        sum(gross_principal_shortfall) AS gross_principal_shortfall,
        sum(net_credit_loss) AS net_credit_loss
    FROM reference
    GROUP BY grade
)
SELECT
    grade_universe.grade,
    coalesce(grade_stats.reference_loans, 0) AS reference_loans,
    coalesce(grade_stats.defaults, 0) AS defaults,
    coalesce(grade_stats.gross_principal_shortfall, 0) AS gross_principal_shortfall,
    coalesce(grade_stats.net_credit_loss, 0) AS net_credit_loss,
    (
        coalesce(grade_stats.defaults, 0)
        + {{pd_smoothing_observations}} * overall.overall_pd
    ) / (
        coalesce(grade_stats.reference_loans, 0) + {{pd_smoothing_observations}}
    ) AS benchmark_pd,
    (
        coalesce(grade_stats.net_credit_loss, 0)
        + {{lgd_smoothing_exposure}} * overall.overall_lgd
    ) / (
        coalesce(grade_stats.gross_principal_shortfall, 0)
        + {{lgd_smoothing_exposure}}
    ) AS benchmark_lgd,
    overall.overall_pd,
    overall.overall_lgd
FROM grade_universe
LEFT JOIN grade_stats USING (grade)
CROSS JOIN overall
ORDER BY grade;

CREATE OR REPLACE TABLE mart_expected_loss_scenarios AS
WITH open_book AS (
    SELECT
        loan_id,
        issue_year,
        grade,
        loan_status,
        outstanding_principal,
        is_default_strict
    FROM fact_loan
    WHERE is_open_book
      AND outstanding_principal > 0
      AND grade IS NOT NULL
), scored AS (
    SELECT
        scenario.scenario_key,
        scenario.scenario_name,
        scenario.pd_multiplier,
        open_book.issue_year,
        open_book.grade,
        open_book.loan_status,
        open_book.outstanding_principal,
        CASE
            WHEN open_book.is_default_strict THEN 1.0
            ELSE least(benchmark.benchmark_pd * scenario.pd_multiplier, 1.0)
        END AS scenario_pd,
        benchmark.benchmark_lgd AS scenario_lgd,
        open_book.outstanding_principal
            * CASE
                WHEN open_book.is_default_strict THEN 1.0
                ELSE least(benchmark.benchmark_pd * scenario.pd_multiplier, 1.0)
              END
            * benchmark.benchmark_lgd AS expected_loss
    FROM open_book
    JOIN dim_grade_risk_benchmark AS benchmark USING (grade)
    CROSS JOIN dim_scenario AS scenario
)
SELECT
    scenario_key,
    scenario_name,
    pd_multiplier,
    issue_year,
    grade,
    loan_status,
    count(*) AS loans,
    sum(outstanding_principal) AS exposure_at_default,
    sum(expected_loss) AS expected_loss,
    sum(expected_loss) / nullif(sum(outstanding_principal), 0) AS expected_loss_rate,
    sum(outstanding_principal * scenario_pd) / nullif(sum(outstanding_principal), 0)
        AS exposure_weighted_pd,
    sum(outstanding_principal * scenario_lgd) / nullif(sum(outstanding_principal), 0)
        AS exposure_weighted_lgd
FROM scored
GROUP BY scenario_key, scenario_name, pd_multiplier, issue_year, grade, loan_status
ORDER BY scenario_key, issue_year, grade, loan_status;

CREATE OR REPLACE TABLE mart_expected_loss_summary AS
WITH scenario_totals AS (
    SELECT
        scenario_key,
        scenario_name,
        pd_multiplier,
        sum(loans) AS loans,
        sum(exposure_at_default) AS exposure_at_default,
        sum(expected_loss) AS expected_loss,
        sum(expected_loss) / nullif(sum(exposure_at_default), 0) AS expected_loss_rate,
        sum(exposure_at_default * exposure_weighted_pd)
            / nullif(sum(exposure_at_default), 0) AS exposure_weighted_pd,
        sum(exposure_at_default * exposure_weighted_lgd)
            / nullif(sum(exposure_at_default), 0) AS exposure_weighted_lgd
    FROM mart_expected_loss_scenarios
    GROUP BY scenario_key, scenario_name, pd_multiplier
), baseline AS (
    SELECT expected_loss, expected_loss_rate
    FROM scenario_totals
    WHERE scenario_key = 'baseline'
)
SELECT
    scenario_totals.*,
    scenario_totals.expected_loss - baseline.expected_loss AS expected_loss_change,
    (scenario_totals.expected_loss - baseline.expected_loss)
        / nullif(baseline.expected_loss, 0) AS expected_loss_relative_change,
    100 * (scenario_totals.expected_loss_rate - baseline.expected_loss_rate)
        AS expected_loss_rate_change_pp
FROM scenario_totals
CROSS JOIN baseline
ORDER BY pd_multiplier;

CREATE OR REPLACE TABLE mart_reconciliation_checks AS
WITH checks AS (
    SELECT
        'unique_loan_grain' AS check_name,
        (SELECT count(*) - count(DISTINCT loan_id) FROM fact_loan)::DOUBLE AS actual_value,
        0::DOUBLE AS expected_value,
        0::DOUBLE AS tolerance

    UNION ALL

    SELECT
        'cash_flow_identity',
        count(*) FILTER (
            WHERE total_payment IS NOT NULL
              AND abs(
                  total_payment - (
                      principal_received + interest_received + late_fees_received + recoveries
                  )
              ) > 0.02
        )::DOUBLE,
        0::DOUBLE,
        0::DOUBLE
    FROM fact_loan

    UNION ALL

    SELECT
        'open_book_summary_ead',
        (SELECT outstanding_exposure FROM mart_open_book_summary),
        (SELECT sum(outstanding_principal) FROM fact_loan WHERE is_open_book),
        0.05::DOUBLE

    UNION ALL

    SELECT
        'expected_loss_population_ead',
        (
            SELECT exposure_at_default
            FROM mart_expected_loss_summary
            WHERE scenario_key = 'baseline'
        ),
        (
            SELECT sum(outstanding_principal)
            FROM fact_loan
            WHERE is_open_book AND grade IS NOT NULL
        ),
        0.05::DOUBLE

    UNION ALL

    SELECT
        'scenario_ead_consistency',
        max(exposure_at_default) - min(exposure_at_default),
        0::DOUBLE,
        0.05::DOUBLE
    FROM mart_expected_loss_summary

    UNION ALL

    SELECT
        'lgd_recovery_identity',
        observed_lgd_proxy + observed_recovery_rate,
        1::DOUBLE,
        0.000000001::DOUBLE
    FROM mart_credit_economics_summary
)
SELECT
    check_name,
    actual_value,
    expected_value,
    tolerance,
    abs(actual_value - expected_value) <= tolerance AS passed
FROM checks
ORDER BY check_name;
