# Power BI handoff

The pipeline exports governed CSV tables to `data/powerbi/`. These extracts are the supported Power BI inputs.

Recommended relationships:

- `executive_summary`: disconnected one-row KPI source.
- `vintage_performance`: issue-year grain, filtered by population scope.
- `segment_performance`: segment type and value grain.
- `credit_economics_summary`: one-row historical cash-flow and loss reconciliation.
- `segment_economics`: grade, term, and purpose economics at segment grain.
- `open_book_summary`: one-row current exposure and delinquency position.
- `open_book_segments`: grade, status, term, purpose, and state open-EAD views.
- `expected_loss_summary`: one row per scenario with from-baseline dollar and percentage changes.
- `expected_loss_scenarios`: scenario, issue year, and grade grain.
- `data_quality_summary`: validation and population audit.
- `reconciliation_checks`: executable control totals; every published build must have zero failures.

Dashboard measures must reconcile to the CSV totals before visual polishing begins. A `.pbix` file is intentionally not committed until the semantic model and visuals have been validated in Power BI Desktop.

The raw loan table is not a supported dashboard input. Only governed aggregate extracts should be
published to a browser or hosted serving layer.
