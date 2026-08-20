# Metric catalog

## Population metrics

### Raw loans

Count of data rows in the source file, excluding the header.

### Resolved eligible loans

Loans whose status is in the configured strict default or non-default set and whose issue date, term, and loan amount are valid.

### Fully matured eligible loans

Resolved eligible loans whose issue month plus contractual term is on or before the configured snapshot date.

### Open book

Accounts in Current, In Grace Period, Late, or Default status with positive recorded outstanding
principal. The population is measured at the source extract's observation month and is separate
from the historical maturity population.

### Retention rate

```text
fully matured eligible loans / resolved eligible loans
```

## Credit metrics

### Default rate

```text
strict defaults / resolved eligible loans
```

### Exposure default rate

```text
funded principal on defaulted loans / funded principal on eligible loans
```

Historical exposure uses funded principal. Open-book exposure at default (EAD) uses recorded
outstanding principal.

### Default contribution

```text
segment defaults / portfolio defaults
```

### Risk multiple

```text
segment default rate / portfolio default rate
```

## Change metrics

### Percentage-point change

```text
comparison rate - baseline rate
```

A movement from 15% to 20% is +5 percentage points.

### Relative percentage change

```text
(comparison rate - baseline rate) / baseline rate
```

A movement from 15% to 20% is +33.3% relative.

## Expected-loss metrics

### Benchmark PD

Smoothed observed default rate by grade among fully matured eligible loans.

### Expected loss

```text
outstanding-principal EAD x scenario-adjusted grade PD x grade LGD
```

PD and LGD are estimated from the fully matured historical reference population and applied to the
open book. This is a lifetime benchmark sensitivity, not a conditional remaining-life PD or CECL
accounting estimate.

### Expected-loss rate

```text
expected loss / outstanding-principal EAD
```

## Credit-economics metrics

### Gross principal shortfall

```text
funded principal - principal received
```

Calculated only for charged-off loans and floored at zero.

### Net recovery

```text
recoveries - collection recovery fees
```

Actual net recovery is preserved as a cash measure. For the LGD identity, principal recovery
applied is capped at the gross principal shortfall so it cannot reduce principal loss below zero.

### Net credit loss

```text
gross principal shortfall - principal recovery applied
```

### Observed LGD proxy

```text
net credit loss / gross principal shortfall
```

This uses unpaid principal as a proxy for exposure at charge-off because exact EAD at the default
event is unavailable.

### Loss-to-interest ratio

```text
net credit loss / recorded interest received
```

### Pricing-cushion proxy

```text
(recorded interest - net credit loss) / funded principal
```

It excludes funding costs, operating costs, discounting, and timing; it is not profit or margin.

### Net cash return proxy

```text
(total cash received - collection fees - funded principal) / funded principal
```

This is non-annualized and must not be described as IRR, APR, or accounting return.

## Future model metrics

- ROC-AUC: ranking quality across all thresholds.
- PR-AUC: ranking quality with emphasis on defaults.
- Brier score: squared probability error.
- Calibration gap: predicted rate minus observed rate.
- Top-decile capture: defaults found in highest-risk 10% divided by all defaults.
- Lift: risk-decile default rate divided by portfolio default rate.
- PSI: change in score or feature distribution between time periods.
