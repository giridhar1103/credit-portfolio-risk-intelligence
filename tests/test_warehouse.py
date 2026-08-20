from dataclasses import replace
from pathlib import Path

import duckdb

from credit_portfolio_analytics.config import ProjectConfig
from credit_portfolio_analytics.database import build_warehouse

ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "loans_sample.csv"


def test_build_warehouse_and_exports(tmp_path: Path) -> None:
    base = ProjectConfig.load(ROOT / "config" / "project.toml")
    config = replace(
        base,
        warehouse_path=tmp_path / "test.duckdb",
        powerbi_output_dir=tmp_path / "powerbi",
    )

    counts = build_warehouse(config, source_path=FIXTURE)

    assert counts["fact_loan"] == 6
    assert counts["mart_executive_summary"] == 1
    assert counts["mart_credit_economics_summary"] == 1
    assert counts["mart_open_book_summary"] == 1
    assert counts["mart_expected_loss_summary"] == 3
    assert counts["mart_reconciliation_checks"] == 6
    assert (tmp_path / "powerbi" / "executive_summary.csv").exists()
    assert (tmp_path / "powerbi" / "expected_loss_summary.csv").exists()
    assert (tmp_path / "powerbi" / "credit_economics_summary.csv").exists()
    assert (tmp_path / "powerbi" / "open_book_summary.csv").exists()
    assert (tmp_path / "powerbi" / "reconciliation_checks.csv").exists()

    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        summary = connection.execute(
            "SELECT resolved_loans, matured_loans, resolved_defaults, matured_defaults "
            "FROM mart_executive_summary"
        ).fetchone()
        economics = connection.execute(
            "SELECT funded_exposure, interest_received, net_credit_loss, "
            "observed_recovery_rate, loss_to_interest_ratio "
            "FROM mart_credit_economics_summary"
        ).fetchone()
        open_book = connection.execute(
            "SELECT loans, outstanding_exposure, delinquent_exposure, default_exposure "
            "FROM mart_open_book_summary"
        ).fetchone()
        expected_loss_population = connection.execute(
            "SELECT loans, exposure_at_default FROM mart_expected_loss_summary "
            "WHERE scenario_key = 'baseline'"
        ).fetchone()
        failed_reconciliations = connection.execute(
            "SELECT count(*) FROM mart_reconciliation_checks WHERE NOT passed"
        ).fetchone()[0]
    finally:
        connection.close()

    assert summary == (4, 3, 2, 2)
    assert economics == (50_000, 5_700, 8_600, 400 / 9_000, 8_600 / 5_700)
    assert open_book == (3, 29_000, 6_000, 15_000)
    assert expected_loss_population == (3, 29_000)
    assert failed_reconciliations == 0
