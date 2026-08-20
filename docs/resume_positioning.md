# Résumé positioning

These are evidence-backed drafts for the completed SQL and portfolio-analysis phase. Update them
after the dashboard and temporal model are finished; do not claim the scenario estimates as actual
losses avoided.

## Draft bullets

- Built a tested Python, DuckDB, and SQL pipeline to validate a **151-field source with 2.26M
  consumer-loan records**, publishing eleven reconciled, Power BI-ready analytical tables.
- Quantified incomplete-maturity bias across **$19.41B of resolved funded exposure**, showing
  that the portfolio default rate decreased from **19.98% to 14.87%** after applying a transparent
  contractual-maturity rule (**-5.11 pp; -25.59% relative**).
- Segmented **676K fully matured loans / $8.83B exposure** across grade, term, purpose, geography,
  interest rate, DTI, income, and loan size; identified a **6.80x default-rate spread** between
  grades A and G.
- Reconciled **$1.54B recorded interest** against **$715.7M recovery-adjusted credit loss** and
  quantified the loss-to-interest ratio at **46.42%** for fully matured loans.
- Built an open-book risk view covering **907.9K accounts / $9.51B EAD**, including **$384.2M
  delinquent exposure**, and modeled **$323.9M-$647.7M** incremental expected loss under transparent
  PD stresses and observed-LGD benchmarks.

## Interview framing

Lead with the analytical problem: recent resolved loans can make an overall default rate look worse
because default resolves earlier than successful repayment. Then explain the maturity rule, show the
rate moving from 19.98% to 14.87%, and clarify that the result changes the measurement population—it
does not prove that credit quality improved.

For scenario analysis, distinguish observed data from assumptions. The $323.9M-$647.7M changes are
sensitivity estimates under configured PD multipliers and historical grade-level benchmarks, not
realized losses or savings.
