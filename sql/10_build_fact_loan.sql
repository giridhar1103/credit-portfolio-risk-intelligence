CREATE OR REPLACE TABLE fact_loan AS
WITH source AS (
    SELECT
        row_number() OVER () AS source_row_number,
        trim(id) AS source_loan_id,
        try_cast(trim(loan_amnt) AS DOUBLE) AS loan_amount,
        try_cast(trim(funded_amnt) AS DOUBLE) AS funded_amount,
        try_cast(trim(out_prncp) AS DOUBLE) AS outstanding_principal,
        try_cast(regexp_extract(trim(term), '(36|60)', 1) AS INTEGER) AS term_months,
        try_cast(replace(trim(int_rate), '%', '') AS DOUBLE) AS interest_rate,
        upper(trim(grade)) AS grade,
        upper(trim(sub_grade)) AS sub_grade,
        try_cast(trim(annual_inc) AS DOUBLE) AS annual_income,
        coalesce(
            try_strptime(trim(issue_d), '%b-%Y')::DATE,
            try_strptime(trim(issue_d), '%b-%y')::DATE
        ) AS issue_date,
        trim(loan_status) AS loan_status,
        lower(trim(purpose)) AS purpose,
        try_cast(trim(dti) AS DOUBLE) AS dti,
        upper(trim(addr_state)) AS state,
        trim(earliest_cr_line) AS earliest_credit_line,
        try_cast(trim(total_pymnt) AS DOUBLE) AS total_payment,
        try_cast(trim(total_rec_prncp) AS DOUBLE) AS principal_received,
        try_cast(trim(total_rec_int) AS DOUBLE) AS interest_received,
        try_cast(trim(total_rec_late_fee) AS DOUBLE) AS late_fees_received,
        try_cast(trim(recoveries) AS DOUBLE) AS recoveries,
        try_cast(trim(collection_recovery_fee) AS DOUBLE) AS collection_recovery_fee,
        coalesce(
            try_strptime(trim(last_pymnt_d), '%b-%Y')::DATE,
            try_strptime(trim(last_pymnt_d), '%b-%y')::DATE
        ) AS last_payment_date,
        coalesce(
            try_strptime(trim(last_credit_pull_d), '%b-%Y')::DATE,
            try_strptime(trim(last_credit_pull_d), '%b-%y')::DATE
        ) AS last_credit_pull_date
    FROM read_csv(
        '{{raw_csv_path}}',
        header = true,
        all_varchar = true,
        sample_size = 200000,
        null_padding = true
    )
), classified AS (
    SELECT
        *,
        issue_date + (term_months || ' months')::INTERVAL AS contractual_maturity_date,
        loan_status IN ({{default_statuses}}) AS is_default_strict,
        loan_status IN ({{non_default_statuses}}) AS is_non_default_strict,
        loan_status IN ({{delinquent_statuses}}) AS is_delinquent,
        loan_status IN ({{charged_off_statuses}}) AS is_charged_off,
        loan_status IN ({{open_statuses}})
            AND coalesce(outstanding_principal, 0) > 0 AS is_open_book,
        loan_status IN ({{default_statuses}}, {{non_default_statuses}}) AS is_model_eligible
    FROM source
), economics AS (
    SELECT
        *,
        greatest(
            coalesce(recoveries, 0) - coalesce(collection_recovery_fee, 0),
            0
        ) AS net_recovery,
        CASE
            WHEN is_charged_off THEN greatest(
                coalesce(funded_amount, 0) - coalesce(principal_received, 0),
                0
            )
            ELSE 0
        END AS gross_principal_shortfall
    FROM classified
), losses AS (
    SELECT
        *,
        least(net_recovery, gross_principal_shortfall) AS principal_recovery_applied
    FROM economics
)
SELECT
    coalesce(nullif(source_loan_id, ''), 'row-' || source_row_number::VARCHAR) AS loan_id,
    source_row_number,
    loan_amount,
    funded_amount,
    outstanding_principal,
    term_months,
    interest_rate,
    grade,
    sub_grade,
    annual_income,
    issue_date,
    extract(year FROM issue_date)::INTEGER AS issue_year,
    contractual_maturity_date::DATE AS contractual_maturity_date,
    contractual_maturity_date <= DATE '{{snapshot_date}}' AS is_contractually_mature,
    date_diff('month', issue_date, DATE '{{source_observation_date}}') AS months_on_book,
    greatest(
        term_months - date_diff('month', issue_date, DATE '{{source_observation_date}}'),
        0
    ) AS remaining_contract_months,
    loan_status,
    purpose,
    dti,
    state,
    earliest_credit_line,
    total_payment,
    principal_received,
    interest_received,
    late_fees_received,
    recoveries,
    collection_recovery_fee,
    net_recovery,
    principal_recovery_applied,
    gross_principal_shortfall,
    CASE
        WHEN is_charged_off THEN gross_principal_shortfall - principal_recovery_applied
        ELSE 0
    END AS net_credit_loss,
    coalesce(total_payment, 0) - coalesce(collection_recovery_fee, 0)
        - coalesce(funded_amount, 0) AS net_cash_return,
    last_payment_date,
    last_credit_pull_date,
    is_default_strict,
    is_non_default_strict,
    is_delinquent,
    is_charged_off,
    is_open_book,
    is_model_eligible,
    CASE
        WHEN interest_rate < 10 THEN '<10%'
        WHEN interest_rate < 15 THEN '10-14.99%'
        WHEN interest_rate < 20 THEN '15-19.99%'
        WHEN interest_rate IS NOT NULL THEN '20%+'
    END AS interest_rate_band,
    CASE
        WHEN dti < 10 THEN '<10'
        WHEN dti < 20 THEN '10-19.99'
        WHEN dti < 30 THEN '20-29.99'
        WHEN dti IS NOT NULL THEN '30+'
    END AS dti_band,
    CASE
        WHEN annual_income < 40000 THEN '<$40k'
        WHEN annual_income < 75000 THEN '$40k-$74,999'
        WHEN annual_income < 125000 THEN '$75k-$124,999'
        WHEN annual_income IS NOT NULL THEN '$125k+'
    END AS income_band,
    CASE
        WHEN funded_amount < 5000 THEN '<$5k'
        WHEN funded_amount < 15000 THEN '$5k-$14,999'
        WHEN funded_amount < 25000 THEN '$15k-$24,999'
        WHEN funded_amount IS NOT NULL THEN '$25k+'
    END AS loan_amount_band
FROM losses;
