# Executive credit risk review

_Generated from the DuckDB analytical marts. Snapshot assumption: 2018-12-31._

## Executive summary

- The source contains **2,260,701 accepted-loan records**. Strict resolved outcomes retain
  **1,348,099 loans (59.63%)**; the contractual-maturity rule
  retains **676,302 loans (29.92% of raw and
  50.17% of resolved)**.
- The default rate changes from **19.98%** on all resolved
  loans to **14.87%** on fully matured loans: a
  **-5.11 pp (-25.59%)**
  change. This quantifies incomplete-maturity bias rather than treating the two populations as
  interchangeable.
- On an original-principal basis, the exposure default rate changes from
  **21.56%** to
  **15.02%**, a
  **-6.54 pp (-30.35%)** change.
- The primary decision population is **676,302 loans** representing
  **$8.83B** in funded principal and
  **100,546 strict defaults**.

## Credit economics

- Fully matured loans generated **$1.54B** of recorded interest
  and **$715.7M** of net credit loss after recoveries and collection
  costs.
- Net credit loss equals **8.10% of funded exposure**.
  Charged-off principal produced a **10.81% net recovery
  rate** and **89.19% observed LGD proxy**.
- The non-annualized net cash return proxy is
  **9.36%**. It is a cash multiple-derived diagnostic,
  not IRR, APR, profit, or an accounting return.
- Credit loss consumed **46.42% of recorded interest**,
  leaving a pre-funding-cost pricing-cushion proxy of
  **9.35% of funded exposure**.

## Open-book risk position

The source observation month is **2019-04-01**, inferred from the latest operational date
available in the extract; it is separate from the conservative historical maturity cutoff above.

- **907,904 open accounts** carry
  **$9.51B of outstanding-principal EAD**.
- Delinquent accounts represent **34,084 loans** and
  **$384.2M**, or
  **4.04% of open EAD**.
- The open book has an exposure-weighted contractual rate of
  **13.25%** and weighted seasoning of
  **15.0 months**.
- Open-book delinquent EAD ranges from **1.12% for grade A** (n=196,647) to **14.65% for grade G** (n=2,830), a **13.06x spread**.

## Risk segmentation

Comparisons below are descriptive and include only segments with at least
1,000 matured loans.

- **Grade:** A was 5.50% (n=144,214) versus G at 37.43% (n=2,060), a 31.93 pp gap and 6.80x risk multiple.
- **Interest-rate band:** <10% was 6.98% (n=216,269) versus 20%+ at 31.05% (n=29,970), a 24.07 pp gap and 4.45x risk multiple.
- **DTI band:** <10 was 11.55% (n=132,305) versus 30+ at 20.61% (n=51,478), a 9.06 pp gap and 1.78x risk multiple.
- **Term:** 36 was 13.95% (n=621,022) versus 60 at 25.22% (n=55,280), a 11.28 pp gap and 1.81x risk multiple.
- **Purpose:** car was 11.91% (n=7,850) versus small_business at 24.77% (n=8,796), a 12.86 pp gap and 2.08x risk multiple.

- Grades E-G represent **7.78% of exposure** but
  **13.72% of defaults** (13,797 defaults).
- **debt_consolidation** is the largest purpose-level source of defaults:
  **60.25% of defaults** against
  **60.16% of exposure**.

## Expected-loss sensitivity

Expected loss uses open-book outstanding principal x smoothed historical grade PD x scenario
multiplier x smoothed observed grade LGD. It is a lifetime benchmark sensitivity, not a company
forecast or CECL estimate.

- **Baseline:** $1.30B expected loss, or 13.62% of EAD (weighted PD 15.27%; weighted LGD 89.32%).
- **Moderate Deterioration:** $1.62B, an increase of $323.9M (24.99%) and 3.41 pp versus baseline.
- **Severe Deterioration:** $1.94B, an increase of $647.7M (49.99%) and 6.81 pp versus baseline.

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
