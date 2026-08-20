# Power BI dashboard specification

## Page 1: Executive credit risk summary

- Eligible loans and exposure
- Reported versus maturity-adjusted default rate
- Expected loss by scenario
- Open EAD and delinquent EAD
- Highest-risk segment
- Largest deteriorating vintage
- Management actions and methodology notes

## Page 2: Portfolio segmentation and concentration

- Default rate and exposure by grade/sub-grade
- Purpose, state, term, DTI, income, rate, and loan-size drilldowns
- Risk multiple and default-contribution views
- Concentration matrix using exposure share and default rate

## Page 3: Vintage and maturity analysis

- Resolved versus matured population comparison
- Vintage default-rate trend
- Grade-within-vintage heatmap
- Population retention by issue year
- Maturity-bias explanation

## Page 4: Pricing and credit economics

- Interest received versus net credit loss
- Loss-to-interest ratio
- Recovery rate and observed LGD proxy
- Pricing-cushion and net-cash-return proxies
- Grade, term, and purpose comparisons
- Prominent non-annualized/no-cost-of-funds caveat

## Page 5: Expected loss and scenarios

- Open-book EAD, PD, LGD, and expected-loss reconciliation
- Baseline, moderate, and severe expected loss
- Dollar and percentage change from baseline
- Grade, status, and vintage loss contribution
- Editable scenario assumption table
- Clear distinction between observed results and modeled scenarios

## Page 6: Model performance and drift

- Logistic Regression versus LightGBM
- Discrimination and calibration metrics
- Risk-decile lift and default capture
- Actual versus predicted by year
- PSI and threshold monitoring

This page will be added after modeling outputs exist.

## Visual standard

- Show the population and period in subtitles.
- Use percentage points for rate differences.
- Display both absolute dollars and percentages for loss changes.
- Avoid gauges without decision thresholds.
- Keep every chart tied to a management question.
