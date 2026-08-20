CREATE OR REPLACE TABLE mart_data_quality_summary AS
SELECT 'raw_rows' AS metric, count(*)::DOUBLE AS value FROM fact_loan
UNION ALL
SELECT 'valid_issue_date_rows', count(*) FILTER (WHERE issue_date IS NOT NULL)::DOUBLE FROM fact_loan
UNION ALL
SELECT 'valid_funded_amount_rows', count(*) FILTER (WHERE funded_amount IS NOT NULL)::DOUBLE
FROM fact_loan
UNION ALL
SELECT 'cash_flow_reconciled_rows', count(*) FILTER (
    WHERE abs(
        total_payment - (
            principal_received + interest_received + late_fees_received + recoveries
        )
    ) <= 0.02
)::DOUBLE
FROM fact_loan
UNION ALL
SELECT 'resolved_eligible_rows', count(*) FILTER (WHERE is_model_eligible)::DOUBLE FROM fact_loan
UNION ALL
SELECT 'fully_matured_eligible_rows', count(*) FILTER (
    WHERE is_model_eligible AND is_contractually_mature
)::DOUBLE
FROM fact_loan
UNION ALL
SELECT 'open_book_rows', count(*) FILTER (WHERE is_open_book)::DOUBLE FROM fact_loan
UNION ALL
SELECT 'delinquent_rows', count(*) FILTER (WHERE is_delinquent)::DOUBLE FROM fact_loan;

CREATE OR REPLACE TABLE mart_executive_summary AS
WITH population AS (
    SELECT
        'resolved' AS population_scope,
        count(*) AS loans,
        sum(funded_amount) AS exposure,
        sum(is_default_strict::INTEGER) AS defaults,
        avg(is_default_strict::INTEGER) AS default_rate,
        sum(funded_amount) FILTER (WHERE is_default_strict) / nullif(sum(funded_amount), 0)
            AS exposure_default_rate
    FROM fact_loan
    WHERE is_model_eligible AND issue_date IS NOT NULL AND funded_amount IS NOT NULL

    UNION ALL

    SELECT
        'fully_matured' AS population_scope,
        count(*) AS loans,
        sum(funded_amount) AS exposure,
        sum(is_default_strict::INTEGER) AS defaults,
        avg(is_default_strict::INTEGER) AS default_rate,
        sum(funded_amount) FILTER (WHERE is_default_strict) / nullif(sum(funded_amount), 0)
            AS exposure_default_rate
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND issue_date IS NOT NULL
      AND funded_amount IS NOT NULL
), pivoted AS (
    SELECT
        max(loans) FILTER (WHERE population_scope = 'resolved') AS resolved_loans,
        max(loans) FILTER (WHERE population_scope = 'fully_matured') AS matured_loans,
        max(exposure) FILTER (WHERE population_scope = 'resolved') AS resolved_exposure,
        max(exposure) FILTER (WHERE population_scope = 'fully_matured') AS matured_exposure,
        max(defaults) FILTER (WHERE population_scope = 'resolved') AS resolved_defaults,
        max(defaults) FILTER (WHERE population_scope = 'fully_matured') AS matured_defaults,
        max(default_rate) FILTER (WHERE population_scope = 'resolved') AS resolved_default_rate,
        max(default_rate) FILTER (WHERE population_scope = 'fully_matured') AS matured_default_rate,
        max(exposure_default_rate) FILTER (WHERE population_scope = 'resolved')
            AS resolved_exposure_default_rate,
        max(exposure_default_rate) FILTER (WHERE population_scope = 'fully_matured')
            AS matured_exposure_default_rate
    FROM population
)
SELECT
    *,
    matured_loans / nullif(resolved_loans, 0) AS matured_population_retention_rate,
    100 * (matured_default_rate - resolved_default_rate) AS default_rate_change_pp,
    (matured_default_rate - resolved_default_rate) / nullif(resolved_default_rate, 0)
        AS default_rate_relative_change
FROM pivoted;

CREATE OR REPLACE TABLE mart_vintage_performance AS
WITH scoped AS (
    SELECT 'resolved' AS population_scope, *
    FROM fact_loan
    WHERE is_model_eligible AND issue_date IS NOT NULL AND funded_amount IS NOT NULL

    UNION ALL

    SELECT 'fully_matured' AS population_scope, *
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND issue_date IS NOT NULL
      AND funded_amount IS NOT NULL
)
SELECT
    population_scope,
    issue_year,
    count(*) AS loans,
    sum(funded_amount) AS exposure,
    sum(is_default_strict::INTEGER) AS defaults,
    avg(is_default_strict::INTEGER) AS default_rate,
    sum(funded_amount) FILTER (WHERE is_default_strict) / nullif(sum(funded_amount), 0)
        AS exposure_default_rate
FROM scoped
GROUP BY population_scope, issue_year
ORDER BY population_scope, issue_year;

CREATE OR REPLACE TABLE mart_segment_performance AS
WITH eligible AS (
    SELECT *
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND issue_date IS NOT NULL
      AND funded_amount IS NOT NULL
), portfolio AS (
    SELECT avg(is_default_strict::INTEGER) AS portfolio_default_rate,
           sum(is_default_strict::INTEGER) AS portfolio_defaults,
           sum(funded_amount) AS portfolio_exposure
    FROM eligible
), segments AS (
    SELECT 'grade' AS segment_type, grade AS segment_value,
           funded_amount AS exposure, is_default_strict
    FROM eligible
    UNION ALL
    SELECT 'sub_grade', sub_grade, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'purpose', purpose, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'term', term_months::VARCHAR, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'state', state, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'interest_rate_band', interest_rate_band, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'dti_band', dti_band, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'income_band', income_band, funded_amount, is_default_strict FROM eligible
    UNION ALL
    SELECT 'loan_amount_band', loan_amount_band, funded_amount, is_default_strict FROM eligible
), aggregated AS (
    SELECT
        segment_type,
        segment_value,
        count(*) AS loans,
        sum(exposure) AS exposure,
        sum(is_default_strict::INTEGER) AS defaults,
        avg(is_default_strict::INTEGER) AS default_rate
    FROM segments
    WHERE segment_value IS NOT NULL
    GROUP BY segment_type, segment_value
)
SELECT
    aggregated.*,
    exposure / nullif(portfolio.portfolio_exposure, 0) AS exposure_share,
    defaults / nullif(portfolio.portfolio_defaults, 0) AS default_contribution,
    100 * (default_rate - portfolio.portfolio_default_rate) AS vs_portfolio_pp,
    default_rate / nullif(portfolio.portfolio_default_rate, 0) AS risk_multiple
FROM aggregated
CROSS JOIN portfolio
ORDER BY segment_type, default_rate DESC;

CREATE OR REPLACE TABLE mart_credit_economics_summary AS
WITH eligible AS (
    SELECT *
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND issue_date IS NOT NULL
      AND funded_amount IS NOT NULL
)
SELECT
    count(*) AS loans,
    sum(funded_amount) AS funded_exposure,
    sum(is_default_strict::INTEGER) AS defaults,
    avg(is_default_strict::INTEGER) AS default_rate,
    sum(total_payment) AS total_cash_received,
    sum(principal_received) AS principal_received,
    sum(interest_received) AS interest_received,
    sum(late_fees_received) AS late_fees_received,
    sum(recoveries) AS gross_recoveries,
    sum(collection_recovery_fee) AS collection_cost,
    sum(net_recovery) AS net_recoveries,
    sum(principal_recovery_applied) AS principal_recoveries_applied,
    sum(gross_principal_shortfall) AS gross_principal_shortfall,
    sum(net_credit_loss) AS net_credit_loss,
    sum(principal_recovery_applied) / nullif(sum(gross_principal_shortfall), 0)
        AS observed_recovery_rate,
    sum(net_credit_loss) / nullif(sum(gross_principal_shortfall), 0) AS observed_lgd_proxy,
    sum(net_credit_loss) / nullif(sum(funded_amount), 0) AS net_credit_loss_rate,
    sum(interest_received) / nullif(sum(funded_amount), 0) AS interest_income_rate_proxy,
    sum(net_credit_loss) / nullif(sum(interest_received), 0) AS loss_to_interest_ratio,
    (sum(interest_received) - sum(net_credit_loss)) / nullif(sum(funded_amount), 0)
        AS pricing_cushion_proxy,
    sum(net_cash_return) / nullif(sum(funded_amount), 0) AS net_cash_return_proxy,
    (sum(total_payment) - sum(collection_recovery_fee)) / nullif(sum(funded_amount), 0)
        AS net_cash_multiple
FROM eligible;

CREATE OR REPLACE TABLE mart_segment_economics AS
WITH eligible AS (
    SELECT *
    FROM fact_loan
    WHERE is_model_eligible
      AND is_contractually_mature
      AND issue_date IS NOT NULL
      AND funded_amount IS NOT NULL
), segments AS (
    SELECT 'grade' AS segment_type, grade AS segment_value, * FROM eligible
    UNION ALL
    SELECT 'term', term_months::VARCHAR, * FROM eligible
    UNION ALL
    SELECT 'purpose', purpose, * FROM eligible
)
SELECT
    segment_type,
    segment_value,
    count(*) AS loans,
    sum(funded_amount) AS funded_exposure,
    sum(is_default_strict::INTEGER) AS defaults,
    avg(is_default_strict::INTEGER) AS default_rate,
    sum(interest_received) AS interest_received,
    sum(net_recovery) AS net_recoveries,
    sum(principal_recovery_applied) AS principal_recoveries_applied,
    sum(gross_principal_shortfall) AS gross_principal_shortfall,
    sum(net_credit_loss) AS net_credit_loss,
    sum(net_credit_loss) / nullif(sum(funded_amount), 0) AS net_credit_loss_rate,
    sum(principal_recovery_applied) / nullif(sum(gross_principal_shortfall), 0)
        AS observed_recovery_rate,
    sum(net_credit_loss) / nullif(sum(gross_principal_shortfall), 0) AS observed_lgd_proxy,
    sum(interest_received) / nullif(sum(funded_amount), 0) AS interest_income_rate_proxy,
    sum(net_credit_loss) / nullif(sum(interest_received), 0) AS loss_to_interest_ratio,
    (sum(interest_received) - sum(net_credit_loss)) / nullif(sum(funded_amount), 0)
        AS pricing_cushion_proxy,
    sum(net_cash_return) / nullif(sum(funded_amount), 0) AS net_cash_return_proxy,
    (sum(total_payment) - sum(collection_recovery_fee)) / nullif(sum(funded_amount), 0)
        AS net_cash_multiple
FROM segments
WHERE segment_value IS NOT NULL
GROUP BY segment_type, segment_value
ORDER BY segment_type, default_rate DESC;

CREATE OR REPLACE TABLE mart_open_book_summary AS
WITH open_book AS (
    SELECT * FROM fact_loan WHERE is_open_book
)
SELECT
    count(*) AS loans,
    sum(outstanding_principal) AS outstanding_exposure,
    count(*) FILTER (WHERE loan_status = 'Current') AS current_loans,
    sum(outstanding_principal) FILTER (WHERE loan_status = 'Current') AS current_exposure,
    count(*) FILTER (WHERE is_delinquent) AS delinquent_loans,
    sum(outstanding_principal) FILTER (WHERE is_delinquent) AS delinquent_exposure,
    count(*) FILTER (WHERE loan_status = 'Default') AS default_loans,
    sum(outstanding_principal) FILTER (WHERE loan_status = 'Default') AS default_exposure,
    sum(outstanding_principal) FILTER (WHERE is_delinquent)
        / nullif(sum(outstanding_principal), 0) AS delinquent_exposure_rate,
    sum(outstanding_principal * interest_rate) / nullif(sum(outstanding_principal), 0)
        AS weighted_average_interest_rate,
    sum(outstanding_principal * months_on_book) / nullif(sum(outstanding_principal), 0)
        AS exposure_weighted_months_on_book
FROM open_book;

CREATE OR REPLACE TABLE mart_open_book_segments AS
WITH open_book AS (
    SELECT * FROM fact_loan WHERE is_open_book
), portfolio AS (
    SELECT sum(outstanding_principal) AS outstanding_exposure FROM open_book
), segments AS (
    SELECT 'grade' AS segment_type, grade AS segment_value, * FROM open_book
    UNION ALL
    SELECT 'status', loan_status, * FROM open_book
    UNION ALL
    SELECT 'term', term_months::VARCHAR, * FROM open_book
    UNION ALL
    SELECT 'purpose', purpose, * FROM open_book
    UNION ALL
    SELECT 'state', state, * FROM open_book
)
SELECT
    segment_type,
    segment_value,
    count(*) AS loans,
    sum(outstanding_principal) AS outstanding_exposure,
    sum(outstanding_principal) / nullif(portfolio.outstanding_exposure, 0) AS exposure_share,
    sum(outstanding_principal * interest_rate) / nullif(sum(outstanding_principal), 0)
        AS weighted_average_interest_rate,
    sum(outstanding_principal) FILTER (WHERE is_delinquent)
        / nullif(sum(outstanding_principal), 0) AS delinquent_exposure_rate,
    sum(outstanding_principal * months_on_book) / nullif(sum(outstanding_principal), 0)
        AS exposure_weighted_months_on_book
FROM segments
CROSS JOIN portfolio
WHERE segment_value IS NOT NULL
GROUP BY segment_type, segment_value, portfolio.outstanding_exposure
ORDER BY segment_type, outstanding_exposure DESC;
