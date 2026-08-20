# Analysis plan

## Decision 1: Is reported portfolio risk biased by incomplete maturity?

Compare resolved loans with the contractually matured subset.

Required outputs:

- population count and exposure before and after maturity filtering;
- retention rate;
- default-rate change in percentage points;
- relative default-rate change;
- vintage results with a minimum population rule.

## Decision 2: Where is credit risk concentrated?

Evaluate grade, sub-grade, purpose, term, state, interest-rate band, DTI band, income band, and loan-size band.

Required outputs:

- loans and exposure;
- default rate;
- difference from portfolio average;
- risk multiple versus portfolio average;
- share of portfolio exposure;
- contribution to observed defaults.

## Decision 3: Did pricing compensate for observed credit loss?

Reconcile recorded interest, unpaid principal, recoveries, collection costs, and total cash
received for the fully matured historical population.

Required outputs:

- gross principal shortfall and recovery-adjusted net credit loss;
- observed recovery-rate and LGD proxies;
- loss-to-interest ratio;
- pricing-cushion and non-annualized net-cash-return proxies;
- grade, term, and purpose comparisons with explicit cost and timing limitations.

## Decision 4: What risk remains in the open book?

Separate positive outstanding-principal exposure from the historical outcome population.

Required outputs:

- current, delinquent, and defaulted open accounts and EAD;
- delinquent-EAD rate;
- exposure-weighted interest rate and months on book;
- risk distribution by grade, status, term, purpose, and state.

## Decision 5: How much loss should management expect?

Estimate PD and LGD benchmarks from fully matured historical loans, apply them to open-book EAD,
and stress PD with transparent scenario multipliers.

Required outputs:

- expected loss dollars and rate by scenario;
- dollar and percentage change from baseline;
- contribution by grade, status, and vintage;
- high-risk exposure and concentration.

## Decision 6: Can high-risk loans be identified reliably?

This phase begins after the full dataset is validated.

Required outputs:

- interpretable Logistic Regression and an optional tree-based challenger;
- temporal train, validation, and test periods;
- ROC-AUC, PR-AUC, Brier score, and calibration error;
- default capture and lift by risk decile;
- threshold results at fixed review capacities;
- yearly performance and population drift.

## Reporting standard

Every key finding must include a numerator, denominator, time period, population definition, and comparison point. Scenario outputs must be labeled as modeled assumptions rather than observed outcomes.
